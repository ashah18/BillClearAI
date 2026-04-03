from django.urls import path
from .views import ProfileView, UserSavingsView

urlpatterns = [
    path("savings/", UserSavingsView.as_view(), name="user-savings"),
    path("profile/", ProfileView.as_view(), name="user-profile"),
]
