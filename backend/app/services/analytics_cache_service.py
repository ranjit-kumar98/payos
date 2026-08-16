import json
from app.services.redis_service import redis_client
import logging

CACHE_KEY_PREFIX = "analytics:"

async def get_analytics_cache(key: str, redis_instance=redis_client):
    full_key = CACHE_KEY_PREFIX + str(key)
    cached = await redis_instance.get(full_key)
    if cached is None:
        return None
    try:
        return json.loads(cached)
    except Exception as e:
        logging.error(f"Error decoding cache data for key {full_key}: {e}")
        return None

async def set_analytics_cache(key: str, data, expires_seconds: int = 300, redis_instance=redis_client):
    full_key = CACHE_KEY_PREFIX + str(key)
    try:
        value = json.dumps(data)
        await redis_instance.set(full_key, value, ex=expires_seconds)
        logging.info(f"Cache set for key {full_key} with TTL {expires_seconds}")
    except Exception as e:
        logging.error(f"Error setting cache for key {full_key}: {e}")

async def invalidate_analytics_cache(key: str, redis_instance=redis_client):
    full_key = CACHE_KEY_PREFIX + str(key)
    try:
        await redis_instance.delete(full_key)
        logging.info(f"Cache invalidated for key {full_key}")
    except Exception as e:
        logging.error(f"Error invalidating cache for key {full_key}: {e}")

async def cache_pattern(key: str, fetch_func, expires_seconds: int = 300):
    """
    Reusable cache pattern helper:
    - Try to get cached data from Redis
    - If cache miss, call fetch_func to get data
    - Set cache with TTL
    - Return data
    """
    cached = await get_analytics_cache(key)
    if cached is not None:
        return cached
    data = await fetch_func()
    if data is not None:
        await set_analytics_cache(key, data, expires_seconds=expires_seconds)
    return data
