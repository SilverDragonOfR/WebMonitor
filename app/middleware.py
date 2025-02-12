# app/middleware.py
from fastapi import FastAPI, Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
import redis
import time

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, redis_url: str, limit: int, window: int):
        super().__init__(app)
        self.redis_client = redis.StrictRedis.from_url(redis_url)
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"

        now = int(time.time())
        with self.redis_client.pipeline() as pipe:
            pipe.incr(key)
            pipe.expire(key, self.window)
            count, _ = pipe.execute()

        if count > self.limit:
            reset_time = self.window - (now % self.window)
            headers = {
                "X-RateLimit-Limit": str(self.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(reset_time)
            }
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers=headers
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - count))
        response.headers["X-RateLimit-Reset"] = str(self.window - (now % self.window))
        return response