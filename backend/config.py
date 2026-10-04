import os
from pathlib import Path

from dotenv import load_dotenv

# Resolve everything relative to backend/ so the app works no matter
# which directory it is started from.
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_path(name, default):
    value = os.getenv(name)
    if not value:
        return str(default)
    path = Path(value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return str(path)


UPLOAD_FOLDER = _env_path("UPLOAD_FOLDER", BASE_DIR / "uploads")
CHROMA_DB_DIR = _env_path("CHROMA_DB_DIR", BASE_DIR / "chroma_db")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

FLASK_DEBUG = _env_bool("FLASK_DEBUG", default=False)
PORT = int(os.getenv("PORT", "5001"))
