import os
import time
import functools
from datetime import datetime, timezone

import redis.asyncio as aioredis

from fastapi import HTTPException, Request
from loguru import logger

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"

_redis_client = None

async def get_redis():
    global _redis_client
    if not redis_enabled:
        return None
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(redis_url, ssl=True, socket_connect_timeout=3)
            await _redis_client.ping()
            logger.info("Connected to Upstash Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable, rate limiting disabled: {e}")
            _redis_client = None
    return _redis_client


RATE_LIMITS = {
    "vsr_submit":    (500,  86400),  # 500/day
    "survey_submit": (500,  86400),  # 500/day
    "mor_submit":    (100,  86400),  # 100/day
    "dashboard":     (1000, 3600),   # 1000/hour
    "auth_attempts": (50,   3600),   # 50/hour
}


def rate_limit(limit_type: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = _find_request(args, kwargs)
            if not request or not redis_enabled:
                return await func(*args, **kwargs)

            tenant_id = _get_tenant_id(kwargs) or "anonymous"
            max_count, window_sec = RATE_LIMITS.get(limit_type, (100, 3600))
            period_key = _period_key(window_sec)
            redis_key = f"rl:{limit_type}:{tenant_id}:{period_key}"

            try:
                r = await get_redis()
                if r:
                    count = await r.incr(redis_key)
                    if count == 1:
                        await r.expire(redis_key, window_sec)
                    if count > max_count:
                        raise HTTPException(
                            status_code=429,
                            detail=f"Rate limit exceeded for {limit_type}. Max {max_count} per {_window_label(window_sec)}.",
                        )
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
