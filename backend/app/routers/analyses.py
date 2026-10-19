from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import AppError
from app.models import Analysis, User, Video
from app.schemas import (
    AnalysisOut,
    AnalysisPage,
    AnalysisSummary,
    Category,
    DeletedOut,
    ErrorOut,
    FeedbackOut,
    Status,
)
from app.security.auth import get_client_id, get_optional_user
from app.settings.conf import settings

router = APIRouter(tags=["analyses"])

ERRORS = {
    401: {"model": ErrorOut},
    404: {"model": ErrorOut},
    422: {"model": ErrorOut},
}


def owner_condition(user: User | None, client_id: str | None):
    if user is not None:
        return Analysis.user_id == user.id
    if client_id is not None:
        return (Analysis.user_id.is_(None)) & (Analysis.client_id == client_id)
    return None


def is_owner(analysis: Analysis, user: User | None, client_id: str | None) -> bool:
    if user is not None:
        return analysis.user_id == user.id or user.is_admin
    if client_id is not None:
        return analysis.user_id is None and analysis.client_id == client_id
    return False


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def expire_if_stale(db: Session, analysis: Analysis) -> None:
    now = datetime.now(UTC)
    if analysis.status == "queued":
        limit = as_utc(analysis.created_at) + timedelta(minutes=settings.queue_timeout_minutes)
        if now > limit:
            analysis.status = "failed"
            analysis.stage = "finished"
            analysis.error_code = "queue_timeout"
            analysis.error_message = "The analysis did not start in time. The worker may be offline."
            analysis.finished_at = now
            db.commit()
    if analysis.status == "running" and analysis.started_at is not None:
        limit = as_utc(analysis.started_at) + timedelta(seconds=settings.task_time_limit_seconds + 120)
        if now > limit:
            analysis.status = "failed"
            analysis.stage = "finished"
            analysis.error_code = "processing_timeout"
            analysis.error_message = "The analysis took too long"
            analysis.finished_at = now
            db.commit()


def find_owned_analysis(db: Session, analysis_id: str, user: User | None, client_id: str | None) -> Analysis:
    if len(analysis_id) > 36:
        raise AppError("not_found", "Analysis not found", 404)
    analysis = db.get(Analysis, analysis_id)
    if analysis is None or not is_owner(analysis, user, client_id):
        raise AppError("not_found", "Analysis not found", 404)
    return analysis


def to_out(analysis: Analysis) -> AnalysisOut:
    feedback = None
    if analysis.feedback:
        feedback = FeedbackOut.model_validate(analysis.feedback[0])
    finished_at = None
    if analysis.finished_at:
        finished_at = as_utc(analysis.finished_at)
    return AnalysisOut(
        id=analysis.id,
        status=analysis.status,
        stage=analysis.stage,
        risk_score=analysis.risk_score,
        category=analysis.category,
        reasons=analysis.reasons or [],
        transcript=analysis.transcript,
        transcript_language=analysis.transcript_language,
        ocr_text=analysis.ocr_text,
        links=analysis.links or [],
        phones=analysis.phones or [],
        qr_codes=analysis.qr_codes or [],
        source_type=analysis.video.source_type,
        source_url=analysis.video.source_url,
        original_filename=analysis.video.original_filename,
        model_version=analysis.model_version,
        error_code=analysis.error_code,
        error_message=analysis.error_message,
        processing_seconds=analysis.processing_seconds,
        created_at=as_utc(analysis.created_at),
        finished_at=finished_at,
        feedback=feedback,
    )


def to_summary(analysis: Analysis) -> AnalysisSummary:
    return AnalysisSummary(
        id=analysis.id,
        status=analysis.status,
        risk_score=analysis.risk_score,
        category=analysis.category,
        source_type=analysis.video.source_type,
        source_url=analysis.video.source_url,
        original_filename=analysis.video.original_filename,
        created_at=as_utc(analysis.created_at),
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut, responses=ERRORS)
def get_analysis(
    analysis_id: str,
    user: User | None = Depends(get_optional_user),
    client_id: str | None = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    analysis = find_owned_analysis(db, analysis_id, user, client_id)
    expire_if_stale(db, analysis)
    return to_out(analysis)


@router.get("/analyses", response_model=AnalysisPage, responses=ERRORS)
def list_analyses(
    page: int = Query(default=1, ge=1, le=10000),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Category | None = None,
    status: Status | None = None,
    min_score: float | None = Query(default=None, ge=0, le=1),
    max_score: float | None = Query(default=None, ge=0, le=1),
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = Query(default=None, max_length=200),
    user: User | None = Depends(get_optional_user),
    client_id: str | None = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    condition = owner_condition(user, client_id)
    if condition is None:
        return AnalysisPage(items=[], total=0, page=page, page_size=page_size)
    query = select(Analysis).join(Video).where(condition)
    if category is not None:
        query = query.where(Analysis.category == category)
    if status is not None:
        query = query.where(Analysis.status == status)
    if min_score is not None:
        query = query.where(Analysis.risk_score >= min_score)
    if max_score is not None:
        query = query.where(Analysis.risk_score <= max_score)
    if date_from is not None:
        query = query.where(Analysis.created_at >= datetime.combine(date_from, time.min, tzinfo=UTC))
    if date_to is not None:
        query = query.where(Analysis.created_at <= datetime.combine(date_to, time.max, tzinfo=UTC))
    if q:
        pattern = "%" + q.strip() + "%"
        query = query.where(or_(Video.source_url.ilike(pattern), Video.original_filename.ilike(pattern)))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    query = query.order_by(Analysis.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = []
    for analysis in db.scalars(query):
        items.append(to_summary(analysis))
    return AnalysisPage(items=items, total=total, page=page, page_size=page_size)


def remove_analysis(db: Session, analysis: Analysis) -> None:
    video = analysis.video
    db.delete(analysis)
    db.flush()
    remaining = db.scalar(select(func.count()).select_from(Analysis).where(Analysis.video_id == video.id)) or 0
    if remaining == 0:
        if video.stored_path:
            Path(video.stored_path).unlink(missing_ok=True)
        db.delete(video)


@router.delete("/analyses/{analysis_id}", status_code=204, responses=ERRORS)
def delete_analysis(
    analysis_id: str,
    user: User | None = Depends(get_optional_user),
    client_id: str | None = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    analysis = find_owned_analysis(db, analysis_id, user, client_id)
    remove_analysis(db, analysis)
    db.commit()


@router.delete("/analyses", response_model=DeletedOut, responses=ERRORS)
def delete_all_analyses(
    user: User | None = Depends(get_optional_user),
    client_id: str | None = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    condition = owner_condition(user, client_id)
    if condition is None:
        return DeletedOut(deleted=0)
    analyses = list(db.scalars(select(Analysis).where(condition, Analysis.status.in_(["done", "failed"]))))
    for analysis in analyses:
        remove_analysis(db, analysis)
    db.commit()
    return DeletedOut(deleted=len(analyses))
