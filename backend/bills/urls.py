from django.urls import path
from .views import (
    BillAnalyzeView,
    BillDetailView,
    BillDisputeView,
    BillListView,
    BillUploadView,
    ChatView,
)

urlpatterns = [
    path("", BillListView.as_view(), name="bill-list"),
    path("upload/", BillUploadView.as_view(), name="bill-upload"),
    path("<int:pk>/", BillDetailView.as_view(), name="bill-detail"),
    path("<int:pk>/analyze/", BillAnalyzeView.as_view(), name="bill-analyze"),
    path("<int:pk>/dispute/", BillDisputeView.as_view(), name="bill-dispute"),
    path("<int:pk>/chat/", ChatView.as_view(), name="bill-chat"),
]
