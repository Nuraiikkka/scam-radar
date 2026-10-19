from app.settings.base import BaseConfig


class LocalConfig(BaseConfig):
    debug: bool = True
    secret_key: str = "local-development-secret-key-change-me-0123456789"
    cors_origins: list[str] = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
    ]
    whisper_model_size: str = "base"
