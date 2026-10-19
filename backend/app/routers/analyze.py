import hashlib
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import AppError
from app.metrics import ANALYSES_CREATED
from app.models import Analysis, User, Video
from app.schemas import AnalyzeCreated, AnalyzeUrlIn, ErrorOut
from app.security.auth import get_client_id, get_optional_user
from app.security.rate_limit import limit_analyze
from app.services import audio, downloader
from app.settings.conf import settings
from app.workers.tasks import analyze_video

logger = logging.getLogger("scamradar.analyze")

router = APIRouter(tags=["analyze"])

CHUNK_SIZE = 1024 * 1024
ALLOWED_CONTENT_TYPES = ["video/", "application/octet-stream"]

REQUEST_BODY = {
    "required": True,
    "content": {
        "application/json": {"schema": {"$ref": "#/components/schemas/AnalyzeUrlIn"}},
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "properties": {"file": {"type": "string", "format": "binary"}},
                "required": ["file"],
            }
        },
    },
}


def check_upload_type(upload: UploadFile) -> str:
    filename = upload.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in settings.allowed_video_extensions:
        allowed = ", ".join(settings.allowed_video_extensions)
        raise AppError("unsupported_file_type", "Only video files are allowed: " + allowed, 415)
    content_type = (upload.content_type or "").lower()
    allowed_type = False
    for prefix in ALLOWED_CONTENT_TYPES:
        if content_type.startswith(prefix):
            allowed_type = True
    if not allowed_type:
        raise AppError("unsupported_file_type", "The file must be a video", 415)
    return extension


def copy_upload(upload: UploadFile, target: Path) -> tuple[int, str]:
    limit = settings.max_upload_mb * 1024 * 1024
    digest = hashlib.sha256()
    size = 0
    with open(target, "wb") as output:
        while True:
            chunk = upload.file.read(CHUNK_SIZE)
            if not chunk:
                break
            size = size + len(chunk)
            if size > limit:
                raise AppError("file_too_large", "The file is larger than " + str(settings.max_upload_mb) + " MB", 413)
            digest.update(chunk)
            output.write(chunk)
    if size == 0:
        raise AppError("empty_file", "The file is empty", 422)
    return size, digest.hexdigest()


def save_upload(upload: UploadFile) -> Video:
    extension = check_upload_type(upload)
    upload_dir = settings.media_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / (uuid.uuid4().hex + extension)
    try:
        size, sha256 = copy_upload(upload, target)
        media = audio.probe_media(target)
    except audio.MediaError as exc:
        target.unlink(missing_ok=True)
        raise AppError(exc.code, exc.message, 415)
    except AppError:
        target.unlink(missing_ok=True)
        raise
    if media.duration > settings.max_video_seconds + 1:
        target.unlink(missing_ok=True)
        raise AppError(
            "video_too_long", "The video is longer than " + str(settings.max_video_seconds) + " seconds", 422
        )
    original_name = Path(upload.filename or "video").name[:255]
    return Video(
        source_type="upload",
        original_filename=original_name,
        sha256=sha256,
        size_bytes=size,
        duration_seconds=media.duration,
        stored_path=str(target),
    )


def url_video(raw: dict) -> Video:
    try:
        payload = AnalyzeUrlIn.model_validate(raw)
    except ValidationError:
        raise AppError("validation_error", 'Send JSON like {"url": "https://www.tiktok.com/..."}', 422)
    try:
        safe_url = downloader.validate_tiktok_url(payload.url)
    except downloader.DownloadError as exc:
        raise AppError(exc.code, exc.message, 422)
    return Video(source_type="url", source_url=safe_url)


async def read_video_from_request(request: Request) -> Video:
    content_type = request.headers.get("content-type", "").lower()
    if content_type.startswith("multipart/form-data"):
        form = await request.form(max_files=1, max_fields=5)
        upload = form.get("file")
        if upload is None or isinstance(upload, str):
            raise AppError("missing_file", "Attach a video in the 'file' field", 422)
        try:
            return await run_in_threadpool(save_upload, upload)
        finally:
            await upload.close()
    if content_type.startswith("application/json"):
        try:
            raw = await request.json()
        except ValueError:
            raise AppError("validation_error", "The body is not valid JSON", 422)
        if not isinstance(raw, dict):
            raise AppError("validation_error", 'Send JSON like {"url": "https://www.tiktok.com/..."}', 422)
        return await run_in_threadpool(url_video, raw)
    raise AppError("unsupported_media_type", "Send a video file (multipart) or JSON with a url", 415)


def enqueue(db: Session, analysis: Analysis) -> None:
    try:
        analyze_video.delay(analysis.id)
    except Exception:
        logger.exception("could not enqueue analysis", extra={"analysis_id": analysis.id})
        analysis.status = "failed"
        analysis.stage = "finished"
        analysis.error_code = "queue_unavailable"
        analysis.error_message = "The analysis queue is not available"
        db.commit()
        raise AppError("queue_unavailable", "The analysis queue is not available, try again later", 503)


@router.post(
    "/analyze",
    status_code=202,
    response_model=AnalyzeCreated,
    openapi_extra={"requestBody": REQUEST_BODY},
    responses={
        413: {"model": ErrorOut},
        415: {"model": ErrorOut},
        422: {"model": ErrorOut},
        429: {"model": ErrorOut},
        503: {"model": ErrorOut},
    },
)
async def analyze(
    request: Request,
    user: User | None = Depends(get_optional_user),
    client_id: str | None = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    user_id = None
    if user is not None:
        user_id = user.id
    await run_in_threadpool(limit_analyze, request, user_id)
    video = await read_video_from_request(request)
    db.add(video)
    db.flush()
    owner_client_id = None
    if user_id is None:
        owner_client_id = client_id
    analysis = Analysis(
        user_id=user_id,
        client_id=owner_client_id,
        video_id=video.id,
        status="queued",
        stage="queued",
        reasons=[],
        links=[],
        phones=[],
        qr_codes=[],
    )
    db.add(analysis)
    db.commit()
    ANALYSES_CREATED.labels(source=video.source_type).inc()
    await run_in_threadpool(enqueue, db, analysis)
    db.refresh(analysis)
    return AnalyzeCreated(analysis_id=analysis.id, status=analysis.status)
