import os
import shutil
import tempfile
from pathlib import Path

TEST_ROOT = Path(tempfile.mkdtemp(prefix="scamradar-tests-"))
os.environ["SCAMRADAR_ENV"] = "test"
os.environ["SCAMRADAR_DATABASE_URL"] = "sqlite:///" + str(TEST_ROOT / "test.db")
os.environ["SCAMRADAR_RATE_LIMIT_STORAGE"] = "memory"
os.environ["SCAMRADAR_CELERY_ALWAYS_EAGER"] = "true"
os.environ["SCAMRADAR_MEDIA_DIR"] = str(TEST_ROOT / "media")
os.environ["SCAMRADAR_LOGS_DIR"] = str(TEST_ROOT / "logs")
os.environ["SCAMRADAR_REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")
os.environ["SCAMRADAR_WHISPER_ENABLED"] = "false"
os.environ["SCAMRADAR_OCR_ENABLED"] = "false"
os.environ["SCAMRADAR_ADMIN_EMAIL"] = "admin@example.com"
os.environ["SCAMRADAR_ADMIN_PASSWORD"] = "admin-password-123"
if "TEST_MODEL_CACHE_DIR" in os.environ:
    os.environ["SCAMRADAR_MODEL_CACHE_DIR"] = os.environ["TEST_MODEL_CACHE_DIR"]

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models import Analysis, Feedback, Signal, User, Video
from app.security import rate_limit
from app.settings.conf import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent
SAMPLES_DIR = REPO_DIR / "data" / "samples"
CLIENT_ID = "test-client-0001"


def alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return config


@pytest.fixture(scope="session", autouse=True)
def database():
    command.upgrade(alembic_config(), "head")
    yield
    shutil.rmtree(TEST_ROOT, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_state():
    rate_limit.counter.reset()
    db = SessionLocal()
    try:
        db.execute(delete(Signal))
        db.execute(delete(Feedback))
        db.execute(delete(Analysis))
        db.execute(delete(Video))
        db.execute(delete(User).where(User.email != settings.admin_email))
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_video():
    return SAMPLES_DIR / "scam_invest_ru.mp4"


def sample_path(name: str) -> Path:
    return SAMPLES_DIR / name


def register(client, email="user@example.com", password="password-123", client_id=None) -> dict:
    headers = {}
    if client_id:
        headers["X-Client-Id"] = client_id
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": "Bearer " + tokens["access_token"]}


def upload(client, path: Path, headers=None, content_type="video/mp4"):
    with open(path, "rb") as handle:
        files = {"file": (path.name, handle, content_type)}
        return client.post("/api/v1/analyze", files=files, headers=headers or {"X-Client-Id": CLIENT_ID})
