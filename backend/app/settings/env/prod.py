from pydantic import model_validator

from app.settings.base import BaseConfig


class ProdConfig(BaseConfig):
    debug: bool = False

    @model_validator(mode="after")
    def check_secrets(self):
        if len(self.secret_key) < 32:
            raise ValueError("SCAMRADAR_SECRET_KEY must be set and at least 32 characters long in production")
        if "*" in self.cors_origins:
            raise ValueError("SCAMRADAR_CORS_ORIGINS must list exact origins in production")
        return self
