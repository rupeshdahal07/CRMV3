"""
Production settings.

Everything security-sensitive is forced on and read from the environment.
At minimum set: DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, DATABASE_URL.
"""

from .base import *  # noqa: F401,F403
from .base import env, env_list

DEBUG = False

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# Hashed, compressed static assets served by WhiteNoise.
STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # noqa: F405

# --- HTTPS / cookie hardening ---
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Fail loudly if the secret key wasn't overridden.
if SECRET_KEY.startswith("django-insecure"):  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY must be set to a real secret in production.")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", "INFO")},
}
