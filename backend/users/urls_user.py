from django.urls import path
from .views import UserSavingsView

urlpatterns = [
    path("savings/", UserSavingsView.as_view(), name="user-savings"),
]
