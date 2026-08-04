import logging
from dataclasses import dataclass
from app.services.redis_service import redis_client

logger = logging.getLogger(__name__)

@dataclass
class RateLimitResult:
    current_count: int
    remaining_requests: int
    ttl_seconds: int
    allowed: bool

async def check_rate_limit(key: str, limit: int, window_seconds: int) -> RateLimitResult:
    redis_key = f"ratelimit:{key}"

    current_count = await redis_client.incr(redis_key)
    if current_count == 1:
        await redis_client.expire(redis_key, window_seconds)

    ttl = await redis_client.ttl(redis_key)
    if ttl < 0:
        # If no TTL is set, set it now
        await redis_client.expire(redis_key, window_seconds)
        ttl = window_seconds

    allowed = current_count <= limit
    remaining_requests = max(limit - current_count, 0)

    logger.info(
        f"Rate limit key: {redis_key} | "
        f"Current count: {current_count} | "
        f"Remaining requests: {remaining_requests} | "
        f"TTL: {ttl} | "
        f"{'Allowed' if allowed else 'Blocked'}"
    )

    return RateLimitResult(
        current_count=current_count,
        remaining_requests=remaining_requests,
        ttl_seconds=ttl,
        allowed=allowed
    )