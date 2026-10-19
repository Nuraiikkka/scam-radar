from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import STATUSES, Analysis

REGISTRY = CollectorRegistry()

HTTP_REQUESTS = Counter(
    "scamradar_http_requests_total",
    "HTTP requests by method, route and status",
    ["method", "route", "status"],
    registry=REGISTRY,
)
HTTP_LATENCY = Histogram(
    "scamradar_http_request_seconds",
    "HTTP request duration in seconds",
    ["method", "route"],
    registry=REGISTRY,
)
ANALYSES_CREATED = Counter(
    "scamradar_analyses_created_total",
    "Analyses created by source type",
    ["source"],
    registry=REGISTRY,
)
ANALYSES_BY_STATUS = Gauge(
    "scamradar_analyses",
    "Analyses in the database by status",
    ["status"],
    registry=REGISTRY,
)
AVERAGE_PROCESSING = Gauge(
    "scamradar_average_processing_seconds",
    "Average processing time of finished analyses",
    registry=REGISTRY,
)


def render_metrics(db: Session) -> tuple[bytes, str]:
    counts = {}
    for status in STATUSES:
        counts[status] = 0
    rows = db.execute(select(Analysis.status, func.count()).group_by(Analysis.status))
    for status, value in rows:
        counts[status] = value
    for status in STATUSES:
        ANALYSES_BY_STATUS.labels(status=status).set(counts[status])
    average = db.scalar(select(func.avg(Analysis.processing_seconds)).where(Analysis.status == "done"))
    AVERAGE_PROCESSING.set(float(average or 0))
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
