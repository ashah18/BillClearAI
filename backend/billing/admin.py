from django.contrib import admin
from .models import BillUploadUsage, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "status", "current_period_end"]
    search_fields = ["user__email", "stripe_customer_id", "stripe_subscription_id"]


@admin.register(BillUploadUsage)
class BillUploadUsageAdmin(admin.ModelAdmin):
    list_display = ["user", "month", "count"]
    list_filter = ["month"]
