import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "drive",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "core.urls"
TEMPLATES = []
WSGI_APPLICATION = "core.wsgi.application"

# Allow the React frontend (any origin during setup; tighten in production)
CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://.*\.vercel\.app$", r"^http://localhost:\d+$"]
CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL", "1") == "1"

DATABASES = {}  # no database needed — this app is stateless

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Google Drive config (set these as environment variables on your host) ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
DRIVE_ROOT_FOLDER_ID = os.environ.get("DRIVE_ROOT_FOLDER_ID", "")
