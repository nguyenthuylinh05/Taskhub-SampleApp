import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

# Application
APP_NAME = os.getenv("APP_NAME", "TaskHub")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
if ENVIRONMENT == "production" and DEBUG:
    raise RuntimeError("DEBUG must be disabled in production")
API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1")

# PostgreSQL
POSTGRES_DB = os.getenv("POSTGRES_DB", "taskhub_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "taskhub_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

if not POSTGRES_PASSWORD:
    raise RuntimeError("POSTGRES_PASSWORD is not configured")

DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    database=POSTGRES_DB,
)

# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY must contain at least 32 characters"
    )

if JWT_ALGORITHM != "HS256":
    raise RuntimeError("Only HS256 algorithm is supported")

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")

if REFRESH_TOKEN_EXPIRE_DAYS <= 0:
    raise RuntimeError("REFRESH_TOKEN_EXPIRE_DAYS must be positive")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"