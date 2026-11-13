from django.contrib import admin

from .models import CustomerFeedback


@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ("category", "name", "email", "status", "created_at")
    list_filter = ("category", "status")
    search_fields = ("name", "email", "message")
    readonly_fields = ("created_at", "updated_at")
