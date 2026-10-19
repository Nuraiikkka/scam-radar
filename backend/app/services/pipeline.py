import logging
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Analysis, Signal
from app.services import audio, downloader, fusion, text_classifier, vision, vision_rules
from app.settings.conf import settings

logger = logging.getLogger("scamradar.pipeline")


class PipelineError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def set_stage(db: Session, analysis: Analysis, stage: str) -> None:
    analysis.stage = stage
    db.commit()
    logger.info("stage changed", extra={"analysis_id": analysis.id, "stage": stage})


def make_work_dir() -> Path:
    base = settings.media_dir / "work"
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="analysis-", dir=base))


def get_video_file(db: Session, analysis: Analysis, work_dir: Path) -> Path:
    video = analysis.video
    if video.source_type == "upload":
        if not video.stored_path or not Path(video.stored_path).exists():
            raise PipelineError("video_missing", "The uploaded video file is no longer available")
        return Path(video.stored_path)
    set_stage(db, analysis, "downloading")
    try:
        downloaded = downloader.download_video(video.source_url or "", work_dir / "download")
    except downloader.DownloadError as exc:
        raise PipelineError(exc.code, exc.message)
    return downloaded["path"]


def save_signals(db: Session, analysis: Analysis, cues: list) -> None:
    for cue in cues:
        db.add(Signal(analysis_id=analysis.id, source=cue.source, kind=cue.kind, value=cue.value, weight=cue.weight))
    if analysis.category and analysis.category != "none":
        db.add(
            Signal(
                analysis_id=analysis.id,
                source="classifier",
                kind="category",
                value=analysis.category,
                weight=analysis.risk_score or 0.0,
            )
        )


def transcript_reason(status: str) -> dict | None:
    if status == "unsupported_language":
        return {
            "source": "speech",
            "code": "unsupported_language",
            "message_en": "In speech: the language is not Russian, English or Kazakh, so speech checks are weaker",
            "message_ru": "В речи: язык не русский, не английский и не казахский, поэтому проверка речи менее точная",
        }
    return None


def check_media(video_path: Path) -> audio.MediaInfo:
    try:
        media = audio.probe_media(video_path)
    except audio.MediaError as exc:
        raise PipelineError(exc.code, exc.message)
    if media.duration > settings.max_video_seconds + 1:
        raise PipelineError(
            "video_too_long", "The video is longer than " + str(settings.max_video_seconds) + " seconds"
        )
    return media


def report_stage(db: Session | None, analysis: Analysis | None, stage: str) -> None:
    if db is None or analysis is None:
        return
    set_stage(db, analysis, stage)


def analyze_local_video(
    video_path: Path, work_dir: Path, db: Session | None = None, analysis: Analysis | None = None
) -> dict:
    media = check_media(video_path)

    report_stage(db, analysis, "listening")
    try:
        transcript = audio.transcribe_video(video_path, work_dir, media)
    except audio.MediaError as exc:
        raise PipelineError(exc.code, exc.message)

    report_stage(db, analysis, "reading_screen")
    vision_result = vision.analyze_video(video_path)

    report_stage(db, analysis, "scoring")
    speech_rules = vision_rules.analyze_text(transcript.text, "speech")
    speech_text = text_classifier.classify_text(transcript.text, "speech")
    screen_text = text_classifier.classify_text(vision_result.ocr_text, "screen_text")
    has_vision_content = bool(vision_result.ocr_text) or bool(vision_result.qr_codes)
    fused = fusion.fuse(speech_text, screen_text, speech_rules["cues"], vision_result.cues, has_vision_content)

    reasons = list(fused.reasons)
    extra = transcript_reason(transcript.status)
    if extra is not None:
        reasons.append(extra)

    return {
        "media": media,
        "fusion": fused,
        "reasons": reasons,
        "transcript": transcript,
        "vision": vision_result,
        "links": vision_rules.unique(vision_result.links + speech_rules["links"]),
        "phones": vision_rules.unique(vision_result.phones + speech_rules["phones"]),
        "cues": speech_rules["cues"] + vision_result.cues,
    }


def finish_success(db: Session, analysis: Analysis, result: dict, started: float) -> None:
    analysis.status = "done"
    analysis.stage = "finished"
    analysis.risk_score = result["fusion"].risk_score
    analysis.category = result["fusion"].category
    analysis.reasons = result["reasons"]
    analysis.transcript = result["transcript"].text or None
    analysis.transcript_language = result["transcript"].language
    analysis.ocr_text = result["vision"].ocr_text or None
    analysis.links = result["links"]
    analysis.phones = result["phones"]
    analysis.qr_codes = result["vision"].qr_codes
    analysis.text_score = result["fusion"].text_score
    analysis.vision_score = result["fusion"].vision_score
    analysis.model_version = text_classifier.model_version()
    analysis.finished_at = datetime.now(UTC)
    analysis.processing_seconds = round(time.monotonic() - started, 2)
    analysis.error_code = None
    analysis.error_message = None
    save_signals(db, analysis, result["cues"])
    db.commit()


def finish_failure(db: Session, analysis: Analysis, code: str, message: str, started: float) -> None:
    db.rollback()
    analysis.status = "failed"
    analysis.stage = "finished"
    analysis.error_code = code
    analysis.error_message = message[:500]
    analysis.finished_at = datetime.now(UTC)
    analysis.processing_seconds = round(time.monotonic() - started, 2)
    db.commit()


def remove_upload_if_expired(db: Session, analysis: Analysis) -> None:
    video = analysis.video
    if settings.video_retention_hours > 0:
        return
    if video.stored_path:
        Path(video.stored_path).unlink(missing_ok=True)
        video.stored_path = None
        video.file_deleted_at = datetime.now(UTC)
        db.commit()


def process(db: Session, analysis: Analysis, work_dir: Path) -> dict:
    video_path = get_video_file(db, analysis, work_dir)
    result = analyze_local_video(video_path, work_dir, db, analysis)
    analysis.video.duration_seconds = result["media"].duration
    return result


def run_analysis(db: Session, analysis_id: str) -> None:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        logger.warning("analysis not found", extra={"analysis_id": analysis_id})
        return
    if analysis.status in ("done", "failed"):
        return
    started = time.monotonic()
    analysis.status = "running"
    analysis.started_at = datetime.now(UTC)
    db.commit()
    work_dir = make_work_dir()
    try:
        result = process(db, analysis, work_dir)
        finish_success(db, analysis, result, started)
        logger.info("analysis done", extra={"analysis_id": analysis.id})
    except PipelineError as exc:
        finish_failure(db, analysis, exc.code, exc.message, started)
        logger.info("analysis failed", extra={"analysis_id": analysis.id, "error_code": exc.code})
    except Exception:
        logger.exception("analysis crashed", extra={"analysis_id": analysis.id})
        finish_failure(db, analysis, "internal_error", "The analysis failed because of a server error", started)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        remove_upload_if_expired(db, analysis)
