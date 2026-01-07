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
    debug: bool = False  # Set via environment variable in development ONLY

    @field_validator("debug")
    @classmethod
    def validate_debug_mode(cls, v: bool, info) -> bool:
        """
        LOW-001 fix: Ensure debug mode is NEVER enabled in production.

        Debug mode can leak sensitive information in error responses.
        This validator forces debug=False in production regardless of config.
        """
        env = info.data.get("env", "development")

        if env == "production" and v is True:
            logger.warning(
                "⚠️  SECURITY: DEBUG=true attempted in production environment. "
                "Forcing DEBUG=false to prevent information leakage."
            )
            return False

        return v

    # API
    api_host: str = "0.0.0.0"  # nosec B104 - Required for Docker container
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "sqlite:///./data/personal_q.db"
    lance_db_path: str = "./data/lancedb"

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

    # ═══════════════════════════════════════════════════════════════════════════
    # LLM Provider API Keys
    # SECURITY CRITICAL: API keys are ONLY read from environment variables.
    # They are NEVER stored in the database. This is a hard requirement.
    # ═══════════════════════════════════════════════════════════════════════════

    # Anthropic (Claude)
    anthropic_api_key: Optional[str] = None
    personal_q_api_key: Optional[str] = None  # Legacy fallback for Anthropic

    # OpenAI (GPT)
    openai_api_key: Optional[str] = None

    # Mistral AI
    mistral_api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Security
    encryption_key: Optional[str] = None  # Fernet key for encrypting sensitive data

    # LOW-004: Trusted proxy configuration for X-Forwarded-For header validation
    # Comma-separated list of trusted proxy IPs or CIDR ranges
    # Example: "127.0.0.1,172.16.0.0/12,10.0.0.0/8"
    trusted_proxies: str = "127.0.0.1,172.16.0.0/12,10.0.0.0/8"

    @property
    def trusted_proxies_list(self) -> set[str]:
        """Parse trusted proxies string into a set of IPs/networks."""
        return {p.strip() for p in self.trusted_proxies.split(",") if p.strip()}

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    jwt_secret_key: Optional[str] = None
    allowed_email: Optional[str] = None  # Comma-separated list of emails allowed to authenticate

    @property
    def allowed_emails_list(self) -> list[str]:
        """Parse ALLOWED_EMAIL string into list of allowed emails."""
        if not self.allowed_email:
            return []
        return [email.strip().lower() for email in self.allowed_email.split(",") if email.strip()]

    def is_email_allowed(self, email: str) -> bool:
        """Check if an email is in the allowed list (case-insensitive)."""
        if not self.allowed_email:
            return False
        return email.lower() in self.allowed_emails_list

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
