import os
import ssl
from datetime import timedelta
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


def _needs_ssl(database_url: str) -> bool:
    """Cloud MySQL (TiDB, etc.) requires SSL. Local MySQL does not."""
    flag = os.getenv("MYSQL_SSL", "").strip().lower()
    if flag in ("1", "true", "yes"):
        return True
    if flag in ("0", "false", "no"):
        return False

    lowered = database_url.lower()
    if "localhost" in lowered or "127.0.0.1" in lowered:
        return False

    if "tidbcloud" in lowered or "tidb." in lowered:
        return True

    return os.getenv("FLASK_ENV") == "production"


def _build_database_uri():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        if database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
        if database_url.startswith("postgresql://") or database_url.startswith(
            "postgres://"
        ):
            raise RuntimeError(
                "DATABASE_URL is PostgreSQL. This app requires MySQL. "
                "Use TiDB Cloud (free MySQL) — see DEPLOY_RENDER.md."
            )
        if not database_url.startswith("mysql+pymysql://"):
            raise RuntimeError(
                "DATABASE_URL must use MySQL. Expected mysql+pymysql://..."
            )
        return database_url

    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "pos_inventory_db")
    return (
        f"mysql+pymysql://{quote_plus(db_user)}:{quote_plus(db_password)}@"
        f"{db_host}:{db_port}/{db_name}"
    )


def _build_engine_options(database_url: str):
    options = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    if _needs_ssl(database_url):
        options["connect_args"] = {"ssl": ssl.create_default_context()}
    return options


_DATABASE_URL = _build_database_uri()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    SQLALCHEMY_DATABASE_URI = _DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _build_engine_options(_DATABASE_URL)

    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # Session & remember-me cookies
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    SESSION_REFRESH_EACH_REQUEST = True

    # CSRF protection (Flask-WTF)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    SHOP_DISPLAY_NAME = os.getenv("SHOP_DISPLAY_NAME", "পস সিস্টেম")
