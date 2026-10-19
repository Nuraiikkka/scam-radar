import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import redis
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Analysis, Video
from app.services import pipeline
from app.settings.conf import settings
from app.workers.celery_app import celery_app

logger = logging.getLogger("scamradar.tasks")

HEARTBEAT_KEY = "scamradar:worker:heartbeat"


@celery_app.task(name="app.workers.tasks.analyze_video")
def analyze_video(analysis_id: str) -> None:
    db = SessionLocal()
    try:
        pipeline.run_analysis(db, analysis_id)
    except SoftTimeLimitExceeded:
        mark_timeout(db, analysis_id)
    finally:
        db.close()


def mark_timeout(db, analysis_id: str) -> None:
    db.rollback()
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        return
    analysis.status = "failed"
    analysis.stage = "finished"
    analysis.error_code = "processing_timeout"
    analysis.error_message = "The analysis took too long"
    analysis.finished_at = datetime.now(UTC)
    db.commit()


def delete_expired_files(db, now: datetime) -> int:
    cutoff = now - timedelta(hours=settings.video_retention_hours)
    query = select(Video).where(Video.stored_path.is_not(None), Video.created_at < cutoff)
    removed = 0
    for video in db.scalars(query):
        has_active = False
        for analysis in video.analyses:
            if analysis.status in ("queued", "running"):
                has_active = True
        if has_active:
            continue
        Path(video.stored_path).unlink(missing_ok=True)
        video.stored_path = None
        video.file_deleted_at = now
        removed = removed + 1
    db.commit()
    return removed


def delete_stale_work_dirs(now: datetime) -> int:
    work_root = settings.media_dir / "work"
    if not work_root.exists():
        return 0
    limit = now.timestamp() - settings.task_time_limit_seconds * 2
    removed = 0
    for folder in work_root.iterdir():
        if folder.is_dir() and folder.stat().st_mtime < limit:
            for path in sorted(folder.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink(missing_ok=True)
                else:
                    path.rmdir()
            folder.rmdir()
            removed = removed + 1
    return removed


@celery_app.task(name="app.workers.tasks.cleanup_expired_videos")
def cleanup_expired_videos() -> int:
    now = datetime.now(UTC)
    db = SessionLocal()
    try:
        removed = delete_expired_files(db, now)
    finally:
        db.close()
    removed = removed + delete_stale_work_dirs(now)
    logger.info("cleanup finished", extra={"status": removed})
    return removed


@celery_app.task(name="app.workers.tasks.heartbeat")
def heartbeat() -> None:
    client = redis.Redis.from_url(settings.redis_url, socket_timeout=2)
    client.set(HEARTBEAT_KEY, str(time.time()), ex=90)
