import time
from fastapi import Request, HTTPException, status, Depends
from .redis_client import get_redis


def rate_limiter(max_requests: int, window_seconds: int):
    """
    Sliding-window-log limiter using a Redis sorted set.
    Usage: Depends(rate_limiter(5, 60)) -> 5 requests per rolling 60s
    """
    def dependency(request: Request, redis_conn=Depends(get_redis)):
        client_ip = request.client.host
        key = f"ratelimit:{request.url.path}:{client_ip}"
        now = time.time()
        window_start = now - window_seconds

        pipe = redis_conn.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        _, _, current_count, _ = pipe.execute()

        if current_count > max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {window_seconds} seconds."
            )

    return dependency