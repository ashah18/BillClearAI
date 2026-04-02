from django.urls import path
from .views import DisputeDetailView

urlpatterns = [
    path("<int:pk>/dispute/<int:dispute_id>/", DisputeDetailView.as_view(), name="dispute-detail"),
]
