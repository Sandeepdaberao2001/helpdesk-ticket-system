import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Config:
    BASE_DIR = BASE_DIR
    FRONTEND_DIR = BASE_DIR.parent / "Frontend"

    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "4"))

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "helpdesk_db")

    CORS_ORIGINS = _split_csv(
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    )
