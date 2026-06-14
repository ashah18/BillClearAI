"""
Django settings for BillClear AI project.
"""

import environ
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

# Read .env file if it exists
environ.Env.read_env(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "storages",
    # Local apps
    "users",
    "bills",
    "disputes",
    "pricing",
    "billing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.ContentSecurityPolicyMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://billclear:billclear@localhost:5432/billclear"),
}

# Custom user model
AUTH_USER_MODEL = "users.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (served by whitenoise in production)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media / file storage
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Use S3 for uploaded bills and generated dispute letters when USE_S3=True.
# Development defaults to local filesystem storage.
USE_S3 = env.bool("USE_S3", default=False)

if USE_S3:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_DEFAULT_ACL = None            # private — inherit bucket settings (no public-read ACL)
    AWS_QUERYSTRING_AUTH = True       # signed, time-limited URLs for any .url access
    AWS_S3_FILE_OVERWRITE = False     # never clobber an existing key
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    default_backend = "storages.backends.s3.S3Storage"
else:
    default_backend = "django.core.files.storage.FileSystemStorage"

# The bills/ and disputes/ S3 key prefixes come from each FileField's upload_to value.
STORAGES = {
    "default": {"BACKEND": default_backend},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "bill_upload": "10/hour",
        "chat": "30/hour",
        "dispute": "10/hour",
        "reanalyze": "5/hour",
        "register": "5/hour",
        "password_reset": "5/hour",
    },
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
}

# JWT settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_COOKIE": "refresh_token",
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SAMESITE": "Lax",
    "AUTH_COOKIE_SECURE": not DEBUG,
}

# CORS settings
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173"],
)
CORS_ALLOW_CREDENTIALS = True

# Anthropic API key
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")

# Stripe (Phase 4C — freemium subscriptions)
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_PRO_PRICE_ID = env("STRIPE_PRO_PRICE_ID", default="")

# Django Sites framework (required by allauth)
SITE_ID = 1

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# django-allauth configuration (allauth 65.x API)
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # Custom User model has no username field
ACCOUNT_EMAIL_VERIFICATION = "none"  # Google already verified the email
SOCIALACCOUNT_AUTO_SIGNUP = True
# If a Google email matches an existing email/password account, connect them
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
# After allauth session login, redirect to our JWT-issuance bridge endpoint
LOGIN_REDIRECT_URL = "/api/auth/google/jwt/"

# Google OAuth app (inline config — no SocialApp DB record needed)
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": env("GOOGLE_CLIENT_ID", default=""),
            "secret": env("GOOGLE_CLIENT_SECRET", default=""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# Frontend URL used for OAuth redirects
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")

# Email configuration
# Single source of truth: if a SendGrid API key is configured, send real emails through
# SendGrid; otherwise fall back to Django's console backend (prints emails to the terminal).
# This guarantees that in development — where no SENDGRID_API_KEY is set — verification and
# password-reset emails are visible in the runserver console.
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@billclear.ai")
SENDGRID_API_KEY = env("SENDGRID_API_KEY", default="")
if SENDGRID_API_KEY:
    EMAIL_BACKEND = env("EMAIL_BACKEND", default="sendgrid_backend.SendgridBackend")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# Keep False so emails are delivered even when DEBUG=True (SendGrid backend respects this flag)
SENDGRID_SANDBOX_MODE_IN_DEBUG = env.bool("SENDGRID_SANDBOX_MODE_IN_DEBUG", default=False)

# ── Security headers ──────────────────────────────────────────────────────────
# Safe in all environments
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True  # legacy header; harmless on modern browsers

# Production-only HTTPS enforcement (gated on DEBUG so dev is unaffected)
if not DEBUG:
    # Railway (and most PaaS proxies) terminate SSL at the edge and forward to
    # Django over HTTP, setting X-Forwarded-Proto: https. Trust that header so
    # Django recognizes the request as secure and SECURE_SSL_REDIRECT doesn't
    # loop forever (ERR_TOO_MANY_REDIRECTS).
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # The frontend (billclearai.app) and backend (*.up.railway.app) live on different
    # registrable domains, so cookies are cross-site from the browser's perspective —
    # SameSite=None (which requires Secure) is needed for them to be sent at all.
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SAMESITE = "None"
    SECURE_HSTS_SECONDS = 31536000          # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# SameSite policy for the JWT refresh-token cookie (set manually in users/views.py).
# In development the frontend (localhost:5173) and backend (localhost:8000) share the
# same site (same registrable domain, different ports), so Lax works. In production
# they're on different domains, requiring None (paired with Secure=True, set above).
JWT_COOKIE_SAMESITE = "Lax" if DEBUG else "None"

# ── Logging ────────────────────────────────────────────────────────────────
# Send app logger output (bills, pricing, disputes, etc.) to stdout/stderr at
# INFO level so diagnostic and exception logs show up in Railway's deployment logs.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
