from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

RATE_LIMITS = {
    "vsr_submit": "10/hour",
    "survey_submit": "5/hour",
    "mor_submit": "20/hour",
    "dashboard": "100/hour",
    "auth_attempts": "5/minute",
    "api_general": "500/hour",
}
