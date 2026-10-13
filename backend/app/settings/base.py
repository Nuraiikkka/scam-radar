from pathlib import Path

from app.settings import conf

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_DIR / "logs"

APP_TITLE = "Scam Radar API"
DEBUG = False

CATEGORIES = ["investment_platform", "pyramid", "betting", "giveaway", "job_offer", "none"]

DATABASE_URL = conf.DATABASE_URL
MOCK = conf.MOCK
MAX_UPLOAD_MB = conf.MAX_UPLOAD_MB
WHISPER_MODEL = conf.WHISPER_MODEL
OCR_LANGS = conf.OCR_LANGS
FRAME_EVERY_SEC = conf.FRAME_EVERY_SEC
MAX_FRAMES = conf.MAX_FRAMES
CORS_ORIGINS = conf.CORS_ORIGINS
LOG_LEVEL = conf.LOG_LEVEL
