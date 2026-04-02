from django.urls import path
from .views import PriceLookupView

urlpatterns = [
    path("<str:cpt_code>/", PriceLookupView.as_view(), name="price-lookup"),
]
