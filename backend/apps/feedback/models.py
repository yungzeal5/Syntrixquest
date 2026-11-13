from django.conf import settings
from django.db import models


class CustomerFeedback(models.Model):
    class Category(models.TextChoices):
        GENERAL = "general", "General"
        WEBSITE = "website", "Website"
        PRODUCT = "product", "Product"
        SERVICE = "service", "Service"

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_submissions",
    )
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    category = models.CharField(
        max_length=12,
        choices=Category.choices,
        default=Category.GENERAL,
    )
    message = models.TextField(max_length=4000)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.NEW,
    )
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "-created_at", "-id"]

    def __str__(self):
        return f"{self.get_category_display()} feedback #{self.pk}"
