import os
import secrets
import sys


class Config:
    API_SECRET_KEY = os.environ.get("API_SECRET_KEY")
    SECRET_HEADER_NAME = "X-API-Key"

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 5432))
    DB_NAME = os.environ.get("DB_NAME", "social_video_db")
    DB_USER = os.environ.get("DB_USER", "videouser")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "changeme123")

    DB_MIN_CONN = int(os.environ.get("DB_MIN_CONN", 1))
    DB_MAX_CONN = int(os.environ.get("DB_MAX_CONN", 10))

    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/downloads")
    MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 300 * 1024 * 1024))

    YTDLP_TIMEOUT = int(os.environ.get("YTDLP_TIMEOUT", 300))

    @classmethod
    def get_database_url(cls):
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"

    @classmethod
    def validate(cls):
        errors = []

        if not cls.API_SECRET_KEY:
            if cls.DEBUG:
                cls.API_SECRET_KEY = secrets.token_urlsafe(32)
                print(f"WARNING: Using auto-generated API key in DEBUG mode: {cls.API_SECRET_KEY}")
            else:
                errors.append("API_SECRET_KEY must be set in production")

        if not cls.DOWNLOAD_DIR:
            errors.append("DOWNLOAD_DIR must be set")

        if not (1 <= cls.PORT <= 65535):
            errors.append(f"PORT must be between 1 and 65535, got {cls.PORT}")

        if not cls.DB_HOST:
            errors.append("DB_HOST must be set")
        if not cls.DB_NAME:
            errors.append("DB_NAME must be set")
        if not cls.DB_USER:
            errors.append("DB_USER must be set")
        if not cls.DB_PASSWORD:
            errors.append("DB_PASSWORD must be set")

        if errors:
            print("Configuration errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(1)

    @classmethod
    def log_config(cls):
        print("Application Configuration:")
        print(f"  HOST: {cls.HOST}")
        print(f"  PORT: {cls.PORT}")
        print(f"  DEBUG: {cls.DEBUG}")
        print(f"  DOWNLOAD_DIR: {cls.DOWNLOAD_DIR}")
        print(f"  MAX_FILE_SIZE: {cls.MAX_FILE_SIZE // 1024 // 1024}MB")
        print(f"  YTDLP_TIMEOUT: {cls.YTDLP_TIMEOUT}s")
        print(f"  API_SECRET_KEY: {'*' * 8} (hidden)")
        print(f"  DB_HOST: {cls.DB_HOST}")
        print(f"  DB_PORT: {cls.DB_PORT}")
        print(f"  DB_NAME: {cls.DB_NAME}")
        print(f"  DB_USER: {cls.DB_USER}")
        print(f"  DB_PASSWORD: {'*' * 8} (hidden)")


Config.validate()

API_SECRET_KEY = Config.API_SECRET_KEY
DOWNLOAD_DIR = Config.DOWNLOAD_DIR
SECRET_HEADER_NAME = Config.SECRET_HEADER_NAME
HOST = Config.HOST
PORT = Config.PORT
DEBUG = Config.DEBUG
DB_HOST = Config.DB_HOST
DB_PORT = Config.DB_PORT
DB_NAME = Config.DB_NAME
DB_USER = Config.DB_USER
DB_PASSWORD = Config.DB_PASSWORD
