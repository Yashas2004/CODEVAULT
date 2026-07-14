from fastapi import Request, HTTPException, status
from .redis_client import redis_client


def rate_limiter(max_requests: int, window_seconds: int):
    """
    Returns a FastAPI dependency that limits a client to `max_requests`
    within `window_seconds`, keyed by client IP.
    Usage: Depends(rate_limiter(5, 60))  -> 5 requests per 60 seconds
    """
    def dependency(request: Request):
        client_ip = request.client.host
        key = f"ratelimit:{request.url.path}:{client_ip}"

        current = redis_client.incr(key)
        if current == 1:
            # first request in this window — set the expiry
            redis_client.expire(key, window_seconds)

        if current > max_requests:
            ttl = redis_client.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {ttl} seconds."
            )

    return dependency