import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.health.hello_task")
def hello_task(name: str):
    print("=====================================")
    print(f"CELERY TASK STARTED")
    print(f"Hello {name}")
    print("Task executed successfully")
    print("=====================================")
    return f"Hello {name} from Celery"
