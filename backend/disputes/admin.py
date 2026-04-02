from django.contrib import admin
from .models import Dispute


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ["id", "bill", "status", "savings_amount", "created_at"]
    list_filter = ["status"]
    filter_horizontal = ["line_items"]
