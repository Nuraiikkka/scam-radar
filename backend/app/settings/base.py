from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCAMRADAR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "local"
    app_name: str = "Scam Radar"
    debug: bool = False

    database_url: str = "postgresql+psycopg://scamradar:scamradar@localhost:5432/scamradar"
    redis_url: str = "redis://localhost:6379/0"
    celery_always_eager: bool = False

    secret_key: str = ""
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    jwt_algorithm: str = "HS256"

    admin_email: str = ""
    admin_password: str = ""

    cors_origins: list[str] = ["http://localhost:8080"]

    trust_proxy_headers: bool = False
    rate_limit_storage: str = "redis"
    rate_limit_anonymous_per_hour: int = 10
    rate_limit_user_per_hour: int = 60
    rate_limit_auth_per_hour: int = 30

    max_upload_mb: int = 60
    max_video_seconds: int = 180
    allowed_video_extensions: list[str] = [".mp4", ".mov", ".webm", ".mkv", ".m4v"]
    allowed_url_hosts: list[str] = [
        "tiktok.com",
        "www.tiktok.com",
        "m.tiktok.com",
        "vm.tiktok.com",
        "vt.tiktok.com",
    ]

    download_timeout_seconds: int = 60
    download_retries: int = 2

    media_dir: Path = BACKEND_DIR / "media"
    logs_dir: Path = BACKEND_DIR / "logs"
    model_cache_dir: Path = BACKEND_DIR / "model_cache"
    video_retention_hours: int = 0
    cleanup_interval_minutes: int = 30

    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_enabled: bool = True

    ocr_enabled: bool = True
    ocr_languages: list[str] = ["ru", "en"]
    ocr_gpu: bool = False
    frame_interval_seconds: float = 2.0
    max_frames: int = 12
    frame_max_width: int = 720

    text_model_path: Path = BACKEND_DIR / "ml" / "models" / "text_model_latest.joblib"

    fusion_text_weight: float = 0.6
    fusion_vision_weight: float = 0.4
    fusion_none_threshold: float = 0.35

    worker_concurrency: int = 2
    queue_timeout_minutes: int = 20
    task_time_limit_seconds: int = 600
