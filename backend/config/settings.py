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
    "axes",
    # Local apps
    "users",
    "bills",
    "disputes",
    "pricing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
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

# Static files
STATIC_URL = "static/"

# Media files
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

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
        "login": "5/hour",  # duration is overridden to 15 min in LoginRateThrottle.__init__
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

# Django Sites framework (required by allauth)
SITE_ID = 1

# Authentication backends
# AxesStandaloneBackend must be first so lockout checks run before other backends
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
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
# In development: set EMAIL_BACKEND=sendgrid_backend.SendgridBackend in .env to send real emails,
# or leave unset to print emails to the console instead.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@billclear.ai")
SENDGRID_API_KEY = env("SENDGRID_API_KEY", default="")
# Keep False so emails are delivered even when DEBUG=True (SendGrid backend respects this flag)
SENDGRID_SANDBOX_MODE_IN_DEBUG = env.bool("SENDGRID_SANDBOX_MODE_IN_DEBUG", default=False)

# ── Security headers ──────────────────────────────────────────────────────────
# Safe in all environments
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True  # legacy header; harmless on modern browsers

# Production-only HTTPS enforcement (gated on DEBUG so dev is unaffected)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000          # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ── django-axes: account lockout after repeated failed login attempts ─────────
AXES_FAILURE_LIMIT = 5                          # lock after 5 failed attempts
AXES_COOLOFF_TIME = timedelta(minutes=15)       # unlock after 15 minutes
AXES_RESET_ON_SUCCESS = True                    # reset failure count on success
AXES_LOCKOUT_CALLABLE = "config.exceptions.axes_lockout_response"
# Track failures by IP + username together (harder to bypass than IP alone)
AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]
