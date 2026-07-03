"""
Base settings shared by every environment.

Environment-specific settings live in ``dev.py`` and ``prod.py`` which import
``*`` from here and then override. Select one with ``DJANGO_SETTINGS_MODULE``
(``config.settings.dev`` by default — see ``manage.py``).

Configuration is read from the environment (12-factor) with safe local
defaults, so the same code runs on a laptop and in production untouched.
"""

import os
from pathlib import Path

# BASE_DIR = the project root (the folder holding manage.py).
# base.py -> settings -> config -> <root>
BASE_DIR = Path(__file__).resolve().parents[2]


def env(key: str, default=None):
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return str(env(key, default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(key: str, default=""):
    raw = env(key, default) or ""
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- Optionally load a .env file if python-dotenv/django-environ style file exists ---
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _, _v = _line.partition("=")
        os.environ.setdefault(_k.strip(), _v.strip())


# --- Security ---
SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "class.nobigo.ai")
CSRF_TRUSTED_ORIGINS = ['https://class.nobigo.ai']


# --- Applications ---
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Local domain apps. Order matters only for admin/label resolution; cross-app
# FKs use string references so any ordering migrates cleanly.
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.leads",
    "apps.consultations",
    "apps.cohorts",
    "apps.scoring",
    "apps.portal",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves compressed static files in production without a CDN.
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
                "apps.core.context_processors.nav_badges",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --- Database ---
# Defaults to SQLite. Set DATABASE_URL for Postgres in production.
_database_url = env("DATABASE_URL")
if _database_url:
    try:
        import dj_database_url  # type: ignore

        DATABASES = {"default": dj_database_url.parse(_database_url, conn_max_age=600)}
    except ImportError:  # pragma: no cover - fallback if helper not installed
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internationalization ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", "Asia/Kathmandu")
USE_I18N = True
USE_TZ = True


# --- Static files ---
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# prod.py swaps this for WhiteNoise's hashed+compressed storage.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


# --- Auth ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
