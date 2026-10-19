import os
import shutil
import time
from datetime import UTC, datetime, timedelta

import pytest
import redis

from app.models import Analysis, Video
from app.services import audio, pipeline, vision_frames
from app.settings.conf import settings
from app.workers import tasks
from tests.conftest import sample_path


def make_upload(db, source: str, created_at=None) -> Analysis:
    upload_dir = settings.media_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / ("copy-" + source)
    shutil.copyfile(sample_path(source), target)
    video = Video(
        source_type="upload",
        original_filename=source,
        stored_path=str(target),
        created_at=created_at or datetime.now(UTC),
    )
    db.add(video)
    db.flush()
    analysis = Analysis(
        video_id=video.id, status="queued", stage="queued", reasons=[], links=[], phones=[], qr_codes=[]
    )
    db.add(analysis)
    db.commit()
    return analysis


def test_worker_task_processes_analysis(db):
    analysis = make_upload(db, "scam_betting_ru.mp4")
    tasks.analyze_video(analysis.id)
    db.expire_all()
    done = db.get(Analysis, analysis.id)
    assert done.status == "done"
    assert 0 <= done.risk_score <= 1


def test_worker_task_ignores_unknown_id():
    tasks.analyze_video("00000000-0000-0000-0000-000000000000")


def test_worker_timeout_marks_failed(db):
    analysis = make_upload(db, "safe_travel_en.mp4")
    tasks.mark_timeout(db, analysis.id)
    db.expire_all()
    assert db.get(Analysis, analysis.id).error_code == "processing_timeout"


def test_missing_upload_fails(db):
    analysis = make_upload(db, "safe_travel_en.mp4")
    os.remove(analysis.video.stored_path)
    tasks.analyze_video(analysis.id)
    db.expire_all()
    assert db.get(Analysis, analysis.id).error_code == "video_missing"


def test_crash_is_reported_as_internal_error(db, monkeypatch):
    def explode(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(pipeline.vision, "analyze_video", explode)
    analysis = make_upload(db, "safe_travel_en.mp4")
    tasks.analyze_video(analysis.id)
    db.expire_all()
    failed = db.get(Analysis, analysis.id)
    assert failed.status == "failed"
    assert failed.error_code == "internal_error"
    assert list((settings.media_dir / "work").glob("*")) == []


def test_cleanup_removes_expired_files(db, monkeypatch):
    monkeypatch.setattr(settings, "video_retention_hours", 1)
    old = make_upload(db, "safe_travel_en.mp4", created_at=datetime.now(UTC) - timedelta(hours=3))
    old.status = "done"
    db.commit()
    fresh = make_upload(db, "safe_cooking_ru.mp4")
    fresh.status = "done"
    db.commit()
    old_path = old.video.stored_path
    removed = tasks.cleanup_expired_videos()
    assert removed >= 1
    assert not os.path.exists(old_path)
    db.expire_all()
    assert db.get(Video, old.video_id).file_deleted_at is not None
    assert db.get(Video, fresh.video_id).stored_path is not None


def test_cleanup_removes_stale_work_dirs(monkeypatch):
    work = settings.media_dir / "work" / "analysis-old"
    work.mkdir(parents=True, exist_ok=True)
    (work / "audio.wav").write_bytes(b"x")
    old_time = time.time() - 100000
    os.utime(work, (old_time, old_time))
    assert tasks.delete_stale_work_dirs(datetime.now(UTC)) == 1
    assert not work.exists()


def test_heartbeat_writes_key():
    tasks.heartbeat()
    client = redis.Redis.from_url(settings.redis_url)
    assert client.exists(tasks.HEARTBEAT_KEY) == 1


def test_probe_media():
    media = audio.probe_media(sample_path("scam_invest_ru.mp4"))
    assert media.has_audio is True
    assert media.duration > 3
    silent = audio.probe_media(sample_path("silent_no_text.mp4"))
    assert silent.has_audio is False


def test_probe_rejects_non_video(tmp_path):
    fake = tmp_path / "fake.mp4"
    fake.write_text("hello")
    with pytest.raises(audio.MediaError) as error:
        audio.probe_media(fake)
    assert error.value.code == "invalid_video"


def test_silent_video_transcript(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "whisper_enabled", True)
    media = audio.probe_media(sample_path("silent_no_text.mp4"))
    result = audio.transcribe_video(sample_path("silent_no_text.mp4"), tmp_path, media)
    assert result.status == "no_audio"


def test_extract_audio_and_rms(tmp_path):
    wav = tmp_path / "a.wav"
    audio.extract_audio(sample_path("scam_invest_en.mp4"), wav)
    assert audio.audio_rms(wav) > audio.SILENCE_RMS


def test_plan_timestamps():
    assert vision_frames.plan_timestamps(0, 2, 10) == [0.0]
    assert len(vision_frames.plan_timestamps(100, 2, 12)) == 12
    assert vision_frames.plan_timestamps(5, 2, 12) == [0.5, 2.5, 4.5]


def test_sample_frames():
    frames = vision_frames.sample_frames(sample_path("scam_invest_ru.mp4"))
    assert 1 <= len(frames) <= settings.max_frames
    assert frames[0].image.shape[1] <= settings.frame_max_width
    assert vision_frames.sample_frames(sample_path("missing.mp4")) == []
