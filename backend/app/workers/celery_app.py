from celery import Celery
from celery.signals import after_setup_logger, worker_process_init

from app.logging_setup import setup_logging
from app.settings.conf import settings

celery_app = Celery("scamradar", broker=settings.redis_url, backend=None, include=["app.workers.tasks"])

celery_app.conf.update(
    task_always_eager=settings.celery_always_eager,
    task_eager_propagates=False,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_time_limit=settings.task_time_limit_seconds,
    task_soft_time_limit=settings.task_time_limit_seconds - 30,
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"visibility_timeout": settings.task_time_limit_seconds * 2},
    worker_hijack_root_logger=False,
    timezone="UTC",
    beat_schedule={
        "cleanup-expired-videos": {
            "task": "app.workers.tasks.cleanup_expired_videos",
            "schedule": settings.cleanup_interval_minutes * 60,
        },
        "worker-heartbeat": {
            "task": "app.workers.tasks.heartbeat",
            "schedule": 30.0,
        },
    },
)


@after_setup_logger.connect
def configure_logging(**kwargs):
    setup_logging(settings.logs_dir, "worker.log", settings.debug)


@worker_process_init.connect
def configure_process_logging(**kwargs):
    setup_logging(settings.logs_dir, "worker.log", settings.debug)
