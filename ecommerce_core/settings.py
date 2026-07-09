import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


IS_DEPLOY_CHECK = "check" in sys.argv and "--deploy" in sys.argv

DEBUG = False if IS_DEPLOY_CHECK else env_bool("DEBUG", False)
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "local-development-secret-key-change-before-production-2026"
    else:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is False.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "127.0.0.1,localhost")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "shop.apps.ShopConfig",
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

if not DEBUG or IS_DEPLOY_CHECK:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "ecommerce_core.urls"

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
                "shop.context_processors.cart_item_count",
            ],
        },
    },
]

WSGI_APPLICATION = "ecommerce_core.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_REDIRECT_URL = "product_list"
LOGOUT_REDIRECT_URL = "product_list"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SECURE_SSL_REDIRECT = (
    True if IS_DEPLOY_CHECK else env_bool("SECURE_SSL_REDIRECT", not DEBUG)
)
SESSION_COOKIE_SECURE = (
    True if IS_DEPLOY_CHECK else env_bool("SESSION_COOKIE_SECURE", not DEBUG)
)
CSRF_COOKIE_SECURE = True if IS_DEPLOY_CHECK else env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = int(
    "31536000"
    if IS_DEPLOY_CHECK
    else os.getenv("SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    True
    if IS_DEPLOY_CHECK
    else env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
)
SECURE_HSTS_PRELOAD = (
    True if IS_DEPLOY_CHECK else env_bool("SECURE_HSTS_PRELOAD", not DEBUG)
)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"
