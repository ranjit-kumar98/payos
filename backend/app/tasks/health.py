import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.health.hello_task")
def hello_task(name: str):
    logger.info(f"hello_task started with name: {name}")
    return f"Hello {name} from Celery"