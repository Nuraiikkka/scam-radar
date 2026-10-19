import redis
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import CategoryOut, HealthOut
from app.settings.conf import settings
from app.version import VERSION
from app.workers.tasks import HEARTBEAT_KEY

router = APIRouter(tags=["meta"])

CATEGORY_INFO = [
    CategoryOut(
        id="investment_platform",
        name_en="Investment platform",
        name_ru="Инвестиционная платформа",
        description_en="Promises big or guaranteed returns from a platform, bot or crypto scheme.",
        description_ru="Обещает большой или гарантированный доход от платформы, бота или криптосхемы.",
    ),
    CategoryOut(
        id="pyramid",
        name_en="Pyramid scheme",
        name_ru="Финансовая пирамида",
        description_en="Pays you mainly for bringing in new people or asks for an entry fee.",
        description_ru="Платит в основном за привлечение новых людей или просит вступительный взнос.",
    ),
    CategoryOut(
        id="betting",
        name_en="Betting / casino",
        name_ru="Ставки / казино",
        description_en="Pushes betting, casinos, fixed matches or sure-win predictions.",
        description_ru="Продвигает ставки, казино, договорные матчи или «верные» прогнозы.",
    ),
    CategoryOut(
        id="giveaway",
        name_en="Fake giveaway",
        name_ru="Фальшивый розыгрыш",
        description_en="Says you won a prize but asks for payment, data or a deposit first.",
        description_ru="Говорит, что вы выиграли приз, но сначала просит оплату, данные или депозит.",
    ),
    CategoryOut(
        id="job_offer",
        name_en="Suspicious job offer",
        name_ru="Подозрительная работа",
        description_en="Easy money for likes or tasks, or asks you to open bank cards for others.",
        description_ru="Лёгкие деньги за лайки или задания, или просит оформить карты на себя.",
    ),
    CategoryOut(
        id="none",
        name_en="No scam signs",
        name_ru="Признаков мошенничества нет",
        description_en="No typical scam signals were found. This is advice, not a guarantee.",
        description_ru="Типичных признаков мошенничества не найдено. Это совет, а не гарантия.",
    ),
]


def check_database(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def redis_client():
    return redis.Redis.from_url(settings.redis_url, socket_timeout=1, socket_connect_timeout=1)


def check_redis() -> bool:
    try:
        return bool(redis_client().ping())
    except redis.RedisError:
        return False


def check_worker() -> bool:
    try:
        return redis_client().exists(HEARTBEAT_KEY) == 1
    except redis.RedisError:
        return False


@router.get("/health", response_model=HealthOut)
def health(response: Response, db: Session = Depends(get_db)):
    database_ok = check_database(db)
    redis_ok = check_redis()
    worker_ok = check_worker()
    status = "ok"
    if not database_ok or not redis_ok or not worker_ok:
        status = "degraded"
    if not database_ok or not redis_ok:
        response.status_code = 503
    return HealthOut(status=status, database=database_ok, redis=redis_ok, worker=worker_ok, version=VERSION)


@router.get("/categories", response_model=list[CategoryOut])
def categories():
    return CATEGORY_INFO
