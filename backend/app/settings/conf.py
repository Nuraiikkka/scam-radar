import os

from app.settings.base import BaseConfig
from app.settings.env.local import LocalConfig
from app.settings.env.prod import ProdConfig


def load_settings() -> BaseConfig:
    env = os.environ.get("SCAMRADAR_ENV", "local").lower()
    if env == "prod":
        return ProdConfig()
    if env == "local" or env == "test":
        return LocalConfig()
    raise ValueError("SCAMRADAR_ENV must be 'local', 'test' or 'prod', got " + env)


settings = load_settings()
