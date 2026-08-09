from celery import Celery
from app.core.config import settings
import re
import logging

def mask_redis_url(url: str) -> str:
    return re.sub(r"(redis://:)(.*)(@)", r"\1****\3", url)

broker_url = settings.REDIS_URL

masked_url = mask_redis_url(broker_url)
logging.info(f"Celery broker URL: {masked_url}")

from celery.schedules import crontab

celery_app = Celery(
    "app",
    broker=broker_url,
    include=[
    "app.tasks.analytics",
    "app.tasks.health",
    "app.tasks.fraud_report",
    "app.tasks.sla_breach_checker",
]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "precompute-analytics-every-15-minute": {
            "task": "app.tasks.analytics.precompute_analytics_task",
            "schedule": crontab(minute="*"),
            "args": ()
        },
        "generate-fraud-report-every-minute": {
            "task": "app.tasks.fraud_report.generate_daily_fraud_report_task",
            "schedule": crontab(minute="*"),
            "args": ()
        },
        "check-sla-breaches-every-hour": {
            "task": "app.tasks.sla_breach_checker.check_sla_breaches_task",
            "schedule": crontab(minute=0, hour="*"),
            "args": ()
        }
    }
)
