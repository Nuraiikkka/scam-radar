from datetime import UTC, date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CATEGORIES, Analysis, User
from app.routers.analyses import owner_condition
from app.schemas import CategoryCount, DailyRisk, StatsOut
from app.security.auth import get_client_id, get_optional_user

router = APIRouter(tags=["stats"])


def to_date(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def only_owner(query, owner):
    if owner is not None:
        query = query.where(owner)
    return query


def count_analyses(db: Session, owner, status: str | None = None, scams_only: bool = False) -> int:
    query = select(func.count()).select_from(Analysis)
    query = only_owner(query, owner)
    if status is not None:
        query = query.where(Analysis.status == status)
    if scams_only:
        query = query.where(Analysis.category != "none")
    result = db.scalar(query)
    if result is None:
        return 0
    return result


def empty_stats() -> StatsOut:
    per_category = []
    for category in CATEGORIES:
        per_category.append(CategoryCount(category=category, count=0))
    return StatsOut(
        total_analyses=0,
        done_analyses=0,
        failed_analyses=0,
        scam_share=0.0,
        average_processing_seconds=None,
        per_category=per_category,
        risk_over_time=[],
    )


@router.get("/stats", response_model=StatsOut)
def get_stats(
    scope: Literal["mine", "all"] = "mine",
    days: int = Query(default=30, ge=1, le=365),
    user: User | None = Depends(get_optional_user),
    client_id: str | None = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    owner = None
    if scope == "mine":
        owner = owner_condition(user, client_id)
        if owner is None:
            return empty_stats()

    total = count_analyses(db, owner)
    done = count_analyses(db, owner, status="done")
    failed = count_analyses(db, owner, status="failed")
    scams = count_analyses(db, owner, status="done", scams_only=True)

    average_query = select(func.avg(Analysis.processing_seconds)).where(Analysis.status == "done")
    average = db.scalar(only_owner(average_query, owner))

    counts = {}
    for category in CATEGORIES:
        counts[category] = 0
    category_query = select(Analysis.category, func.count()).where(Analysis.status == "done")
    category_query = only_owner(category_query, owner).group_by(Analysis.category)
    for category, value in db.execute(category_query):
        if category in counts:
            counts[category] = value
    per_category = []
    for category in CATEGORIES:
        per_category.append(CategoryCount(category=category, count=counts[category]))

    since = datetime.now(UTC) - timedelta(days=days)
    day_column = func.date(Analysis.created_at)
    daily_query = select(day_column, func.count(), func.avg(Analysis.risk_score))
    daily_query = daily_query.where(Analysis.status == "done", Analysis.created_at >= since)
    daily_query = only_owner(daily_query, owner).group_by(day_column).order_by(day_column)
    risk_over_time = []
    for day_value, day_count, day_average in db.execute(daily_query):
        if day_average is None:
            day_average = 0
        risk_over_time.append(
            DailyRisk(day=to_date(day_value), count=day_count, average_risk=round(float(day_average), 4))
        )

    scam_share = 0.0
    if done > 0:
        scam_share = round(scams / done, 4)
    average_seconds = None
    if average is not None:
        average_seconds = round(float(average), 2)
    return StatsOut(
        total_analyses=total,
        done_analyses=done,
        failed_analyses=failed,
        scam_share=scam_share,
        average_processing_seconds=average_seconds,
        per_category=per_category,
        risk_over_time=risk_over_time,
    )
