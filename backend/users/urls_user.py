from django.urls import path
from .views import ProfileView, UserDisclosureView, UserSavingsView

urlpatterns = [
    path("savings/", UserSavingsView.as_view(), name="user-savings"),
    path("profile/", ProfileView.as_view(), name="user-profile"),
    path("disclosure/", UserDisclosureView.as_view(), name="user-disclosure"),
]
