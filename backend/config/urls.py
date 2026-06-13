"""
URL configuration for BillClear AI project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import GoogleJWTView

urlpatterns = [
    path("admin/", admin.site.urls),
    # allauth handles the full Google OAuth dance at /accounts/google/login/
    # and /accounts/google/login/callback/
    path("accounts/", include("allauth.urls")),
    # After allauth session login, bridge to SimpleJWT tokens
    path("api/auth/google/jwt/", GoogleJWTView.as_view(), name="google-jwt"),
    path("api/auth/", include("users.urls")),
    path("api/bills/", include("bills.urls")),
    path("api/bills/", include("disputes.urls")),
    path("api/pricing/", include("pricing.urls")),
    path("api/user/", include("users.urls_user")),
    path("api/billing/", include("billing.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
