import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent


def decimal_from_env(name: str) -> Decimal | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ImproperlyConfigured(f"{name} must be a decimal number.") from exc


def bool_from_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = bool_from_env("DJANGO_DEBUG", False)
ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if host]
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "audit",
    "companies",
    "documents",
    "extraction",
    "accounting",
    "standardization",
    "review",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL", "sqlite:///" + str(PROJECT_DIR / "db.sqlite3"))
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = os.getenv("STATIC_URL", "/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/companies/"
LOGOUT_REDIRECT_URL = "/login/"

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
OPENAI_BALANCE_EXTRACTION_ENABLED = (
    os.getenv("OPENAI_BALANCE_EXTRACTION_ENABLED", "false").lower() == "true"
)
OPENAI_BALANCE_EXTRACTION_MODEL = os.getenv("OPENAI_BALANCE_EXTRACTION_MODEL", "gpt-5.4-mini")
OPENAI_INPUT_USD_PER_MILLION_TOKENS = decimal_from_env("OPENAI_INPUT_USD_PER_MILLION_TOKENS")
OPENAI_CACHED_INPUT_USD_PER_MILLION_TOKENS = decimal_from_env(
    "OPENAI_CACHED_INPUT_USD_PER_MILLION_TOKENS"
)
OPENAI_OUTPUT_USD_PER_MILLION_TOKENS = decimal_from_env("OPENAI_OUTPUT_USD_PER_MILLION_TOKENS")
USD_BRL_EXCHANGE_RATE = decimal_from_env("USD_BRL_EXCHANGE_RATE")
ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = (
    decimal_from_env("ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE") or Decimal("0.01")
)
ACCOUNTING_VALIDATION_RATIO_TOLERANCE = (
    decimal_from_env("ACCOUNTING_VALIDATION_RATIO_TOLERANCE") or Decimal("0.01")
)
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
SESSION_COOKIE_SECURE = bool_from_env("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = bool_from_env("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
