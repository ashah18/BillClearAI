"""
URL configuration for BillClear AI project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/bills/", include("bills.urls")),
    path("api/bills/", include("disputes.urls")),
    path("api/pricing/", include("pricing.urls")),
    path("api/user/", include("users.urls_user")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
