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
    api_host: str = "0.0.0.0"  # nosec B104 - Required for Docker container
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

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: Optional[str], info) -> Optional[str]:
        """
        Validate ENCRYPTION_KEY is set in production.

        SECURITY FIX (HIGH-002): Enforce encryption key requirement
        - Required in production for encrypting API keys
        - Must be a valid Fernet key (44 characters, base64url encoded)
        - Auto-generate in development with warning
        """
        env = info.data.get("env", "development")

        if env == "production":
            if not v:
                raise ValueError(
                    "ENCRYPTION_KEY is required in production for encrypting API keys. "
                    "Generate a Fernet key with: "
                    "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )

            # Validate it's a proper Fernet key
            if len(v) != 44 or not v.endswith("="):
                raise ValueError(
                    "ENCRYPTION_KEY must be a valid Fernet key (44 characters, base64url encoded). "
                    "Generate with: "
                    "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )

        elif not v:
            # Development: Generate key with warning
            from cryptography.fernet import Fernet

            generated_key = Fernet.generate_key().decode()
            logger.warning(
                "⚠️  ENCRYPTION_KEY not set. Generated a random key for this session. "
                "For persistence, set ENCRYPTION_KEY in .env with: "
                f"ENCRYPTION_KEY={generated_key}"
            )
            return generated_key

        return v

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
                # SECURITY FIX: Never use hardcoded secrets (CVE-002)
                # Generate a unique secret for each instance
                import secrets

                generated_secret = secrets.token_urlsafe(32)
                logger.warning(
                    "⚠️  JWT_SECRET_KEY not set. Generated a random secret for this session. "
                    "For production, set JWT_SECRET_KEY in .env with: "
                    f"JWT_SECRET_KEY={generated_secret}"
                )
                return generated_secret

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

            # SECURITY FIX: Block wildcard CORS in production (HIGH-001)
            if "*" in origins:
                raise ValueError(
                    "CORS wildcard '*' is not allowed in production. "
                    "Please specify exact allowed origins in CORS_ORIGINS environment variable."
                )

        return origins


# Global settings instance
settings = Settings()
