from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class CeleryTestRequest(BaseModel):
    name: str

@router.post("/celery-test")
async def celery_test(request: CeleryTestRequest):
    from app.tasks.health import hello_task

    hello_task.delay(request.name)

    return {
        "status": "queued",
        "task": "hello_task"
    }