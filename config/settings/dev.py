"""Local development settings."""

from .base import *  # noqa: F401,F403
from .base import env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)

# Convenience for LAN testing (e.g. a phone on the same WiFi). Dev-only.
ALLOWED_HOSTS = ["*"]

# Show emails in the console instead of sending them.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = ["127.0.0.1"]
