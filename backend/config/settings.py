"""
Application configuration settings.
"""

import logging
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Application
    app_name: str = "Personal-Q AI Agent Manager"
    app_version: str = "1.0.0"
    env: str = "development"
    debug: bool = False  # Set via environment variable in development

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "sqlite:///./data/personal_q.db"
    chroma_db_path: str = "./data/chromadb"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Memory
    memory_retention_days: int = 90

    # LLM Defaults
    default_model: str = "claude-3-5-sonnet-20241022"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Security
    encryption_key: Optional[str] = None  # Fernet key for encrypting sensitive data

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    jwt_secret_key: Optional[str] = None
    allowed_email: Optional[str] = None  # Single user email allowed to authenticate

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: Optional[str], info) -> Optional[str]:
        """
        Validate JWT_SECRET_KEY is set and meets minimum security requirements.

        SECURITY: JWT_SECRET_KEY must be:
        - At least 32 characters long
        - Set in production environments
        """
        # Check if OAuth is enabled by checking google_client_id
        oauth_enabled = info.data.get("google_client_id") is not None
        env = info.data.get("env", "development")

        if oauth_enabled:
            if not v:
                if env == "production":
                    raise ValueError(
                        "JWT_SECRET_KEY is required when Google OAuth is "
                        "enabled in production. Generate a secure key with: "
                        "python -c 'import secrets; "
                        "print(secrets.token_urlsafe(32))'"
                    )
                else:
                    logger.warning(
                        "⚠️  JWT_SECRET_KEY not set. Using insecure default for development. "
                        "Set JWT_SECRET_KEY in .env for production."
                    )
                    return "INSECURE_DEV_SECRET_CHANGE_IN_PRODUCTION"

            if len(v) < 32:
                raise ValueError(
                    f"JWT_SECRET_KEY must be at least 32 characters long "
                    f"(current: {len(v)}). Generate a secure key with: "
                    "python -c 'import secrets; "
                    "print(secrets.token_urlsafe(32))'"
                )

        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list with production validation."""
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

        # SECURITY FIX (HIGH-003): Validate CORS origins in production
        # Prevent developer localhost origins from leaking into production
        if self.env == "production":
            # Check for localhost/127.0.0.1 in production
            localhost_origins = [o for o in origins if "localhost" in o or "127.0.0.1" in o]
            if localhost_origins:
                raise ValueError(
                    f"CORS_ORIGINS contains localhost in production: {localhost_origins}\n"
                    "Please set CORS_ORIGINS to your production domain(s)."
                )

            # Warn about wildcard
            if "*" in origins:
                if len(origins) > 1:
                    raise ValueError("Cannot use wildcard '*' with other CORS origins")
                logger.warning("⚠️  WILDCARD CORS: All origins allowed (security risk)")

        return origins


# Global settings instance
settings = Settings()
