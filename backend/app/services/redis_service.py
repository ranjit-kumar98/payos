import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def store_session(user_id: str, token_id: str, expires_seconds: int = 86400):
    key = f"session:{user_id}:{token_id}"
    await redis_client.set(key, "active", ex=expires_seconds)

async def check_session(user_id: str, token_id: str) -> bool:
    key = f"session:{user_id}:{token_id}"
    return await redis_client.exists(key) == 1

async def remove_session(user_id: str, token_id: str):
    key = f"session:{user_id}:{token_id}"
    await redis_client.delete(key)
