"""Application configuration objects.

Every secret is read from the environment. The only default secret key lives
in DevelopmentConfig and ProductionConfig refuses to start without a real one.
"""

import os
from datetime import timedelta


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    """Settings shared by every environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Session hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", "30"))
    )
    WTF_CSRF_TIME_LIMIT = None

    # Domain settings
    CREDENTIAL_ID_PREFIX = os.environ.get("CREDENTIAL_ID_PREFIX", "QVS")
    ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE", "10"))
    PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", "12"))
    # Trust X-Forwarded-* headers. Only safe when a trusted reverse proxy sits
    # in front and overwrites them -- otherwise a client can forge its own
    # scheme and address. Off by default; on in production (Fly.io's edge).
    TRUST_PROXY_HEADERS = _bool("TRUST_PROXY_HEADERS", False)
    RATELIMIT_ENABLED = _bool("RATELIMIT_ENABLED", True)
    RATELIMIT_LOGIN = os.environ.get("RATELIMIT_LOGIN", "10 per minute")
    RATELIMIT_VERIFY = os.environ.get("RATELIMIT_VERIFY", "30 per minute")

    @staticmethod
    def normalise_database_url(url: str) -> str:
        """Fly.io/Heroku hand out ``postgres://``; SQLAlchemy 2 wants a driver."""
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = BaseConfig.normalise_database_url(
        os.environ.get("DATABASE_URL", "sqlite:///qvs-dev.db")
    )


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    # Fixed so tests are deterministic. This config is selected only by
    # create_app("testing") and can never be reached in a deployed process.
    # Not a credential: it signs nothing outside the test process.
    SECRET_KEY = "testing-key"  # nosec B105
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    PASSWORD_MIN_LENGTH = 12


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"
    # Fly.io terminates TLS at its edge and forwards X-Forwarded-Proto. Without
    # this the application sees every request as plain HTTP, so it would never
    # emit HSTS and would log the proxy's address instead of the client's.
    TRUST_PROXY_HEADERS = True

    def __init__(self) -> None:
        if os.environ.get("SECRET_KEY") in (None, "", "dev-only-insecure-key"):
            raise RuntimeError("SECRET_KEY must be set to a strong random value in production.")
        self.SECRET_KEY = os.environ["SECRET_KEY"]
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL must be set in production.")
        self.SQLALCHEMY_DATABASE_URI = self.normalise_database_url(database_url)


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    """Return a config object/class for ``name`` (defaults to ``FLASK_ENV``)."""
    name = (name or os.environ.get("FLASK_ENV") or "development").lower()
    config = CONFIG_MAP.get(name, DevelopmentConfig)
    return config() if config is ProductionConfig else config
