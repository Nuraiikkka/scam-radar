import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings
from app.db import Base, engine
from app import models
from app.routers import analyze, meta

settings.LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=str(settings.LOGS_DIR / "app.log"),
    level=settings.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_TITLE, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(analyze.router)
