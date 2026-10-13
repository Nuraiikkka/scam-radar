from pathlib import Path
from decouple import AutoConfig, Csv

BASE_DIR = Path(__file__).resolve().parent

config = AutoConfig(search_path=str(BASE_DIR))

ENV_ID = config("SCAMRADAR_ENV_ID", default="local")
DATABASE_URL = config("SCAMRADAR_DATABASE_URL", default="sqlite:///./scamradar.db")
MOCK = config("SCAMRADAR_MOCK", default=False, cast=bool)
MAX_UPLOAD_MB = config("SCAMRADAR_MAX_UPLOAD_MB", default=100, cast=int)
WHISPER_MODEL = config("SCAMRADAR_WHISPER_MODEL", default="base")
OCR_LANGS = config("SCAMRADAR_OCR_LANGS", default="en,ru", cast=Csv())
FRAME_EVERY_SEC = config("SCAMRADAR_FRAME_EVERY_SEC", default=2.0, cast=float)
MAX_FRAMES = config("SCAMRADAR_MAX_FRAMES", default=15, cast=int)
CORS_ORIGINS = config("SCAMRADAR_CORS_ORIGINS", default="*", cast=Csv())
LOG_LEVEL = config("SCAMRADAR_LOG_LEVEL", default="INFO")
