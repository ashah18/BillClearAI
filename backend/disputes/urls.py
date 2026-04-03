from django.urls import path
from .views import DisputeDetailView, DisputeDownloadView, DisputeListView

urlpatterns = [
    path("<int:pk>/disputes/", DisputeListView.as_view(), name="dispute-list"),
    path("<int:pk>/dispute/<int:dispute_id>/", DisputeDetailView.as_view(), name="dispute-detail"),
    path("<int:pk>/dispute/<int:dispute_id>/download/", DisputeDownloadView.as_view(), name="dispute-download"),
]
