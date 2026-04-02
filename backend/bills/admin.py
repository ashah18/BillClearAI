from django.contrib import admin
from .models import Bill, ChatMessage, LineItem


class LineItemInline(admin.TabularInline):
    model = LineItem
    extra = 0
    readonly_fields = ["description_plain", "risk_level", "error_type"]


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "provider_name", "total_charged", "status", "created_at"]
    list_filter = ["status", "facility_type"]
    search_fields = ["user__email", "provider_name"]
    inlines = [LineItemInline]


@admin.register(LineItem)
class LineItemAdmin(admin.ModelAdmin):
    list_display = ["id", "bill", "cpt_code", "charged_amount", "risk_level", "error_type"]
    list_filter = ["risk_level", "error_type"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "bill", "user", "role", "created_at"]
    list_filter = ["role"]
