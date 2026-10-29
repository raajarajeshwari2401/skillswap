import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base configuration with robust defaults."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "skillswap-dev-secret-key-3806e501")
    # Database config: defaults to local SQLite for frictionless local dev,
    # overrides with PostgreSQL DATABASE_URL in cloud/production.
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        # Fix legacy Heroku/Render dialect scheme
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url or f"sqlite:///{BASE_DIR / 'skillswap.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Security & Session Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")
    WTF_CSRF_ENABLED = os.environ.get("WTF_CSRF_ENABLED", "True").lower() in ("true", "1")

    # Socket.IO configuration
    SOCKETIO_ASYNC_MODE = os.environ.get("SOCKETIO_ASYNC_MODE", "threading")
    RAW_SOCKET_HOST = os.environ.get("RAW_SOCKET_HOST", "127.0.0.1")
    RAW_SOCKET_PORT = int(os.environ.get("RAW_SOCKET_PORT", 9099))

    # Skill Difficulty & Points Calculation Config (Academic SymPy baseline)
    BASE_POINTS_PER_30_MIN = 10.0
    MULTIPLIER_BEGINNER = 1.0
    MULTIPLIER_INTERMEDIATE = 1.5
    MULTIPLIER_ADVANCED = 2.0
    MAX_PREPARATION_BONUS = 15.0
    INITIAL_WELCOME_POINTS = 50.0  # College student welcome points grant


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration with an in-memory SQLite database."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    RAW_SOCKET_PORT = 9199


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": ProductionConfig,
}
