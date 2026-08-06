import redis.asyncio as redis
from app.core.config import settings

# Dedicated Redis client for Celery tasks to avoid event loop conflicts with FastAPI Redis client
celery_redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)