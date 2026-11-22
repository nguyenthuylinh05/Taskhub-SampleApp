"""Application configuration settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "TaskHub"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    # PostgreSQL
    POSTGRES_DB: str = "taskhub_db"
    POSTGRES_USER: str = "taskhub_user"
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = Field(default=5432, gt=0, le=65535)
    POSTGRES_TEST_DB: str = "taskhub_test_db"

    # JWT
    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = Field(default=6379, gt=0, le=65535)
    REDIS_DB: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate security-sensitive application settings."""
        if self.ENVIRONMENT == "production" and self.DEBUG:
            raise ValueError("DEBUG must be disabled in production")

        if len(self.JWT_SECRET_KEY.get_secret_value()) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must contain at least 32 characters"
            )

        return self

    @property
    def DATABASE_URL(self) -> URL:
        """Build the asynchronous PostgreSQL connection URL."""
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    @property
    def TEST_DATABASE_URL(self) -> URL:
        """Build the asynchronous test database connection URL."""
        return self.DATABASE_URL.set(database=self.POSTGRES_TEST_DB)

    @property
    def REDIS_URL(self) -> str:
        """Build the Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()

# Module-level exports for existing application imports.
APP_NAME = settings.APP_NAME
APP_VERSION = settings.APP_VERSION
ENVIRONMENT = settings.ENVIRONMENT
DEBUG = settings.DEBUG
API_V1_PREFIX = settings.API_V1_PREFIX

POSTGRES_DB = settings.POSTGRES_DB
POSTGRES_USER = settings.POSTGRES_USER
POSTGRES_PASSWORD = settings.POSTGRES_PASSWORD.get_secret_value()
POSTGRES_HOST = settings.POSTGRES_HOST
POSTGRES_PORT = settings.POSTGRES_PORT
POSTGRES_TEST_DB = settings.POSTGRES_TEST_DB

DATABASE_URL = settings.DATABASE_URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

JWT_SECRET_KEY = settings.JWT_SECRET_KEY.get_secret_value()
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
REFRESH_TOKEN_EXPIRE_SECONDS = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_DB = settings.REDIS_DB
REDIS_URL = settings.REDIS_URL
