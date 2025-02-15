# app/middleware.py
from fastapi import FastAPI, Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
import redis
import time

# Define a custom middleware 'RateLimiterMiddleware' for Rate Limiting purposes
class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, redis_url: str, limit: int, window: int):
        super().__init__(app)
        self.redis_client = redis.StrictRedis.from_url(redis_url) # Creating a Redis client using the provided Redis URL
        self.limit = limit # Setting the request limit for the rate limiter.
        self.window = window # Setting the time window (in seconds) for the rate limiter

    # Handle each incoming request
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host # The client's IP address from the request
        key = f"rate_limit:{client_ip}" # Constructing a unique key for Redis to store the request count for each client IP

        now = int(time.time())
        with self.redis_client.pipeline() as pipe:
            pipe.incr(key)# Incrementing the request count for the client IP in Redis. If the key doesn't exist, it's initialized to 1.
            pipe.expire(key, self.window) # Set an expiry time for key
            count, _ = pipe.execute() # 'count' will be the incremented value

        # Check if the request count for the client IP exceeds the defined limit.
        if count > self.limit:
            reset_time = self.window - (now % self.window)
            headers = {
                # Defining headers to be included in the rate limit exceeded response
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
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - count)) # Add the remaining requests
        response.headers["X-RateLimit-Reset"] = str(self.window - (now % self.window)) # Add the reset time to the response headers
        return response