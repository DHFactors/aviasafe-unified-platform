import time
from collections import defaultdict
from typing import Callable, Dict, List

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    _requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60.0
        max_requests = settings.RATE_LIMIT_PER_MINUTE

        self._requests[ip] = [t for t in self._requests[ip] if now - t < window]
        if len(self._requests[ip]) >= max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

        self._requests[ip].append(now)
        return await call_next(request)
