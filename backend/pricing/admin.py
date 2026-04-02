from django.contrib import admin
from .models import CPTPriceCache


@admin.register(CPTPriceCache)
class CPTPriceCacheAdmin(admin.ModelAdmin):
    list_display = ["cpt_code", "description", "national_average", "created_at"]
    search_fields = ["cpt_code", "description"]
