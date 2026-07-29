import redis.asyncio as redis
import json
import logging
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def store_session(user_id: str, token_id: str, email: str, full_name: str, is_active: bool = True, is_admin: bool = False, expires_seconds: int = 86400):
    key = f"session:{user_id}:{token_id}"
    session_data = {
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "is_active": is_active,
        "is_admin": is_admin,
        "login_timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }
    try:
        await redis_client.set(key, json.dumps(session_data), ex=expires_seconds)
        logging.info(f"Redis session created: {key}")
    except Exception as e:
        logging.error(f"Error storing Redis session {key}: {e}")
        raise

async def get_session(user_id: str, token_id: str):
    key = f"session:{user_id}:{token_id}"
    try:
        data = await redis_client.get(key)
        if data is None:
            logging.info(f"Redis session miss: {key}")
            return None
        logging.info(f"Redis session hit: {key}")
        return json.loads(data)
    except Exception as e:
        logging.error(f"Error retrieving Redis session {key}: {e}")
        return None

async def check_session(user_id: str, token_id: str) -> bool:
    key = f"session:{user_id}:{token_id}"
    try:
        exists = await redis_client.exists(key) == 1
        if exists:
            logging.info(f"Redis session hit: {key}")
        else:
            logging.info(f"Redis session miss: {key}")
        return exists
    except Exception as e:
        logging.error(f"Error checking Redis session {key}: {e}")
        return False

async def remove_session(user_id: str, token_id: str):
    key = f"session:{user_id}:{token_id}"
    try:
        await redis_client.delete(key)
        logging.info(f"Redis session deleted: {key}")
    except Exception as e:
        logging.error(f"Error deleting Redis session {key}: {e}")
        raise
