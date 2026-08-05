import os
import functools
from datetime import datetime, timezone, timedelta

import redis.asyncio as aioredis

from fastapi import HTTPException, Request
from loguru import logger

from app.core.config import settings

redis_url = settings.REDIS_URL or os.getenv("REDIS_URL", "")
redis_enabled = settings.REDIS_ENABLED or os.getenv("REDIS_ENABLED", "").lower() == "true"

if not redis_url:
    logger.warning("REDIS_URL not set — rate limiting disabled. Set in Render dashboard or backend/.env")

_redis_client = None

async def get_redis():
    global _redis_client
    if not redis_enabled:
        return None
    if _redis_client is None:
        try:
            kwargs = dict(socket_connect_timeout=3)
            if not redis_url.startswith("rediss://"):
                from redis.asyncio.connection import SSLConnection
                kwargs["connection_class"] = SSLConnection
            kwargs["ssl_cert_reqs"] = "none"
            _redis_client = aioredis.from_url(redis_url, **kwargs)
            await _redis_client.ping()
            logger.info("Connected to Upstash Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable, rate limiting disabled: {e}")
            _redis_client = None
    return _redis_client


RATE_LIMITS = {
    "vsr_submit":    (50,  86400),   # 50/day  (beta)
    "survey_submit": (100, 86400),   # 100/day (beta)
    "mor_submit":    (20,  86400),   # 20/day  (beta)
    "dashboard":     (500, 3600),    # 500/hour (beta)
    "auth_attempts": (200, 3600),    # 200/hour (beta; safety net for shared login attempts)
}


def rate_limit(limit_type: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = _find_request(args, kwargs)
            if not request or not redis_enabled:
                return await func(*args, **kwargs)

            tenant_id = _get_tenant_id(kwargs)
            bucket_key = f"tenant:{tenant_id}" if tenant_id else f"ip:{_get_client_ip(request)}"
            max_count, window_sec = RATE_LIMITS.get(limit_type, (100, 3600))
            period_key = _period_key(window_sec)
            redis_key = f"rl:{limit_type}:{bucket_key}:{period_key}"

            try:
                r = await get_redis()
                if not r:
                    return await func(*args, **kwargs)

                count = await r.incr(redis_key)
                if count == 1:
                    await r.expire(redis_key, window_sec)

                ttl = await r.ttl(redis_key)
                remaining = max(0, max_count - count)

                resp_headers = {
                    "X-RateLimit-Limit": str(max_count),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(int(_reset_epoch(window_sec))),
                }

                if count > max_count:
                    retry_after = max(1, int(ttl))
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "success": False,
                            "error": "Rate limit exceeded",
                            "message": f"Max {max_count} requests per {_window_label(window_sec)}. Try again in {retry_after}s.",
                            "retry_after": retry_after,
                            "limit": max_count,
                            "remaining": 0,
                            "reset": _reset_iso(window_sec),
                        },
                        headers=resp_headers,
                    )

                # Attach rate limit info to request state for downstream use
                request.state.rate_limit = {
                    "limit": max_count,
                    "remaining": remaining,
                    "reset": _reset_iso(window_sec),
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Rate limit check failed: {e}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def _find_request(args, kwargs):
    for arg in args:
        if isinstance(arg, Request):
            return arg
    return kwargs.get("request")


def _get_tenant_id(kwargs: dict) -> str:
    user = kwargs.get("user") or kwargs.get("current_user")
    if user and isinstance(user, dict):
        return user.get("tenant_id")
    return None


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _period_key(window_sec: int) -> str:
    if window_sec >= 86400:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return datetime.now(timezone.utc).strftime("%Y-%m-%d:%H")


def _window_label(window_sec: int) -> str:
    if window_sec >= 86400:
        return "day"
    if window_sec >= 3600:
        return "hour"
    return f"{window_sec}s"


def _reset_epoch(window_sec: int) -> float:
    now = datetime.now(timezone.utc)
    if window_sec >= 86400:
        reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        reset = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return reset.timestamp()


def _reset_iso(window_sec: int) -> str:
    epoch = _reset_epoch(window_sec)
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
