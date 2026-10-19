import logging
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.db import SessionLocal, get_db
from app.errors import error_response, install_error_handlers
from app.logging_setup import request_id_var, setup_logging
from app.metrics import HTTP_LATENCY, HTTP_REQUESTS, render_metrics
from app.models import User
from app.routers import admin, analyses, analyze, auth, feedback, meta, stats
from app.security.auth import hash_password
from app.settings.conf import settings
from app.version import VERSION

logger = logging.getLogger("scamradar.api")

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")
API_PREFIX = "/api/v1"
MAX_REQUEST_BYTES = (settings.max_upload_mb + 1) * 1024 * 1024


def ensure_admin_user() -> None:
    if not settings.admin_email or not settings.admin_password:
        return
    db = SessionLocal()
    try:
        email = settings.admin_email.lower()
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            password_hash = hash_password(settings.admin_password)
            db.add(User(email=email, password_hash=password_hash, is_admin=True))
        else:
            user.is_admin = True
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.info("admin user was created by another worker")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    ensure_admin_user()
    logger.info("api started", extra={"stage": settings.env})
    yield


def make_request_id(request: Request) -> str:
    incoming = request.headers.get("x-request-id", "")
    if REQUEST_ID_PATTERN.match(incoming):
        return incoming
    return uuid.uuid4().hex


def is_too_large(request: Request) -> bool:
    length = request.headers.get("content-length")
    if length is None or not length.isdigit():
        return False
    return int(length) > MAX_REQUEST_BYTES


def route_label(request: Request) -> str:
    route = request.scope.get("route")
    if route is None:
        return "unmatched"
    return route.path


async def add_request_id(request: Request, call_next):
    request_id = make_request_id(request)
    request.state.request_id = request_id
    request_id_var.set(request_id)

    if is_too_large(request):
        message = "The request is larger than " + str(settings.max_upload_mb) + " MB"
        response = error_response(request, 413, "file_too_large", message)
        response.headers["X-Request-ID"] = request_id
        return response

    started = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - started

    route = route_label(request)
    HTTP_REQUESTS.labels(method=request.method, route=route, status=str(response.status_code)).inc()
    HTTP_LATENCY.labels(method=request.method, route=route).observe(duration)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    log_data = {
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": round(duration * 1000, 1),
    }
    logger.info("request", extra=log_data)
    return response


setup_logging(settings.logs_dir, "api.log", settings.debug)

app = FastAPI(
    title="Scam Radar API",
    version=VERSION,
    lifespan=lifespan,
    docs_url=API_PREFIX + "/docs",
    redoc_url=None,
    openapi_url=API_PREFIX + "/openapi.json",
)
install_error_handlers(app)

app.add_middleware(BaseHTTPMiddleware, dispatch=add_request_id)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Client-Id", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

app.include_router(analyze.router, prefix=API_PREFIX)
app.include_router(analyses.router, prefix=API_PREFIX)
app.include_router(feedback.router, prefix=API_PREFIX)
app.include_router(stats.router, prefix=API_PREFIX)
app.include_router(meta.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)

admin.setup_admin(app)


@app.get("/metrics", include_in_schema=False)
def metrics(db: Session = Depends(get_db)):
    body, content_type = render_metrics(db)
    return Response(content=body, media_type=content_type)


def build_openapi() -> dict:
    if app.openapi_schema is not None:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    all_schemas = schema["components"]["schemas"]
    all_schemas.pop("HTTPValidationError", None)
    all_schemas.pop("ValidationError", None)
    error_content = {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorOut"}}}
    for path in schema["paths"].values():
        for operation in path.values():
            responses = operation.get("responses", {})
            if "422" in responses:
                responses["422"]["description"] = "Validation Error"
                responses["422"]["content"] = error_content
    app.openapi_schema = schema
    return schema


app.openapi = build_openapi
