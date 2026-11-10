from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
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

    # PostgreSQL
    POSTGRES_DB: str = "taskhub_db"
    POSTGRES_USER: str = "taskhub_user"
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # JWT
    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.DEBUG:
            raise ValueError("DEBUG must be disabled in production")

        if len(self.JWT_SECRET_KEY.get_secret_value()) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must contain at least 32 characters"
            )

        if self.JWT_ALGORITHM != "HS256":
            raise ValueError("Only HS256 algorithm is supported")

        if self.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")

        if self.REFRESH_TOKEN_EXPIRE_DAYS <= 0:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be positive")

        return self

    @property
    def DATABASE_URL(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    @property
    def REDIS_URL(self) -> str:
        return (
            f"redis://{self.REDIS_HOST}:"
            f"{self.REDIS_PORT}/{self.REDIS_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Backward-compatible exports for existing modules.
APP_NAME = settings.APP_NAME
APP_VERSION = settings.APP_VERSION
ENVIRONMENT = settings.ENVIRONMENT
DEBUG = settings.DEBUG
API_V1_PREFIX = settings.API_V1_PREFIX

DATABASE_URL = settings.DATABASE_URL

JWT_SECRET_KEY = settings.JWT_SECRET_KEY.get_secret_value()
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

REDIS_URL = settings.REDIS_URL