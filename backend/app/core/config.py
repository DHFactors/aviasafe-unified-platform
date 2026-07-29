from pydantic_settings import BaseSettings
from typing import List, Optional
from enum import Enum


class AuthRole(str, Enum):
    AIRLINE_ADMIN = "AIRLINE_ADMIN"
    CAAN_SMD = "CAAN_SMD"
    SUPER_ADMIN = "SUPER_ADMIN"
    USER = "USER"


class Settings(BaseSettings):
    # ── API ──
    API_VERSION: str = "1.0.0"
    API_PREFIX_AUTH: str = "/api/v1/auth"
    API_PREFIX_REPORTS: str = "/api/v1/reports"
    API_PREFIX_DASHBOARD: str = "/api/v1/dashboard"
    API_PREFIX_ADMIN: str = "/api/v1/admin"
    API_PREFIX_HAZARDS: str = "/api/v1/hazards"
    API_PREFIX_CAN_CAP: str = "/api/v1/cans"
    API_PREFIX_VERIFICATION: str = "/api/v1/verification"
    API_PREFIX_REPORTING: str = "/api/v1/reporting"
    API_PREFIX_FLIGHT_DIVERSIONS: str = "/api/v1/flight-diversions"
    API_PREFIX_AUTH_LEGACY: str = "/api/auth"
    API_PREFIX_REPORTS_LEGACY: str = "/api/reports"
    API_PREFIX_DASHBOARD_LEGACY: str = "/api/dashboard"
    API_PREFIX_ADMIN_LEGACY: str = "/api/admin"
    API_PREFIX_HAZARDS_LEGACY: str = "/api/hazards"
    API_PREFIX_CAN_CAP_LEGACY: str = "/api/cans"
    API_PREFIX_VERIFICATION_LEGACY: str = "/api/verification"
    API_PREFIX_REPORTING_LEGACY: str = "/api/reporting"
    API_PREFIX_FLIGHT_DIVERSIONS_LEGACY: str = "/api/flight-diversions"
    DEBUG: bool = False

    # ── CORS ──
    ALLOWED_ORIGINS: str = "https://gap-analysis-ssp.web.app,http://localhost:3000,http://localhost:8000"

    # ── Firebase ──
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None
    FIREBASE_COLLECTION_TENANTS: str = "tenants"
    FIREBASE_COLLECTION_REPORTS: str = "reports"
    FIREBASE_COLLECTION_METADATA: str = "metadata"
    FIREBASE_DOCUMENT_INFO: str = "info"
    FIREBASE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"

    # ── JWT ──
    JWT_ALGORITHM: str = "RS256"
    JWT_EXPIRES_IN: int = 3600

    # ── AI / Gemini ──
    AI_MODEL: str = "gemini-2.0-pro-exp-02-05"
    AI_PROMPT_VERSION: str = "2.0"
    AI_NARRATIVE_TRUNCATE: int = 5000
    AI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # ── Repository / Pagination ──
    REPO_CACHE_TTL_SECONDS: int = 60
    REPO_DEFAULT_PAGE_SIZE: int = 20
    REPO_MAX_PAGE_SIZE: int = 100
    REPO_QUERY_LIMIT: int = 5000

    # ── Dashboard defaults ──
    DASHBOARD_DEFAULT_DAYS: int = 90
    DASHBOARD_TREND_DAYS: int = 180
    DASHBOARD_RECENT_PAGE_SIZE: int = 10
    DASHBOARD_ADMIN_USAGE_DAYS: int = 30
    DASHBOARD_ADMIN_SYSTEM_DAYS: int = 7
    DASHBOARD_ADMIN_TENANT_DAYS: int = 30

    # ── Roles ──
    ROLE_DEFAULT: str = "USER"
    ROLE_DEFAULT_REGISTRATION: str = "AIRLINE_ADMIN"
    CROSS_TENANT_ROLES: List[str] = ["CAAN_SMD", "SUPER_ADMIN"]
    SUPER_ADMIN_ROLES: List[str] = ["SUPER_ADMIN"]

    # ── Upstash Redis ──
    REDIS_URL: str = ""
    REDIS_ENABLED: bool = False

    # ── Rate limiting ──
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True, "extra": "ignore"}


settings = Settings()
