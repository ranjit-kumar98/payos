import json
from app.services.redis_service import redis_client

CACHE_KEY_PREFIX = "analytics:overview:"

async def get_analytics_cache(merchant_id: int, redis_instance=redis_client):
    key = f"{CACHE_KEY_PREFIX}{merchant_id}"
    cached = await redis_instance.get(key)
    if cached is None:
        return None
    return json.loads(cached)

async def set_analytics_cache(merchant_id: int, analytics_data: dict, expires_seconds: int = 300, redis_instance=redis_client):
    key = f"{CACHE_KEY_PREFIX}{merchant_id}"
    value = json.dumps(analytics_data)
    await redis_instance.set(key, value, ex=expires_seconds)

async def invalidate_analytics_cache(merchant_id: int, redis_instance=redis_client):
    key = f"{CACHE_KEY_PREFIX}{merchant_id}"
    await redis_instance.delete(key)
