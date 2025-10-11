"""
Application configuration settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
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

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
