from django.contrib import admin
from .models import CPTPriceCache, LocalityGPCI, ProcedureRVU, ZipToLocality


@admin.register(CPTPriceCache)
class CPTPriceCacheAdmin(admin.ModelAdmin):
    list_display = ["cpt_code", "description", "national_average", "created_at"]
    search_fields = ["cpt_code", "description"]


@admin.register(ProcedureRVU)
class ProcedureRVUAdmin(admin.ModelAdmin):
    list_display = ["hcpc", "modifier", "short_description", "proc_stat",
                    "rvu_work", "full_nfac_pe", "full_fac_pe", "rvu_mp", "conv_fact", "year"]
    list_filter = ["proc_stat", "year"]
    search_fields = ["hcpc", "short_description"]
    ordering = ["hcpc", "modifier"]


@admin.register(LocalityGPCI)
class LocalityGPCIAdmin(admin.ModelAdmin):
    list_display = ["locality", "loc_description", "mac", "gpci_work", "gpci_pe", "gpci_mp", "year"]
    list_filter = ["year"]
    search_fields = ["locality", "loc_description", "mac"]
    ordering = ["locality"]


@admin.register(ZipToLocality)
class ZipToLocalityAdmin(admin.ModelAdmin):
    list_display = ["zip_code", "state", "carrier", "locality_code", "year"]
    list_filter = ["state", "year"]
    search_fields = ["zip_code", "state", "carrier"]
    ordering = ["zip_code"]
