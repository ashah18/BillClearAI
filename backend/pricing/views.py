from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import CPTPriceCache
from .serializers import CPTPriceSerializer


class PriceLookupView(APIView):
    """
    Public endpoint that returns fair pricing data for a given CPT code.
    Checks the local cache first; returns a 404 if the code is not in the cache.
    CMS fee schedule import is a Phase 2 feature.
    """

    permission_classes = [AllowAny]

    def get(self, request, cpt_code):
        try:
            price_entry = CPTPriceCache.objects.get(cpt_code=cpt_code)
        except CPTPriceCache.DoesNotExist:
            return Response(
                {"detail": f"No pricing data found for CPT code {cpt_code}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CPTPriceSerializer(price_entry)
        return Response(serializer.data)
