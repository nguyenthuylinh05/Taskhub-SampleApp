import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

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
