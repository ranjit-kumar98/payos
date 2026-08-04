import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.services.rate_limit_service import check_rate_limit

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 100
DEFAULT_WINDOW_SECONDS = 60

async def rate_limit_dependency(request: Request):
    client_ip = request.client.host
    result = await check_rate_limit(client_ip, DEFAULT_LIMIT, DEFAULT_WINDOW_SECONDS)

    logger.info(
        f"Rate limit check for IP: {client_ip} | "
        f"Current count: {result.current_count} | "
        f"Remaining requests: {result.remaining_requests} | "
        f"TTL: {result.ttl_seconds} | "
        f"{'Allowed' if result.allowed else 'Blocked'}"
    )

    if not result.allowed:
        headers = {
            "Retry-After": str(result.ttl_seconds),
            "X-RateLimit-Limit": str(DEFAULT_LIMIT),
            "X-RateLimit-Remaining": str(result.remaining_requests),
            "X-RateLimit-Reset": str(result.ttl_seconds),
        }
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
            headers=headers
        )