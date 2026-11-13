from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True, unique=True)
    phone_number = models.CharField(max_length=32, blank=True)
    marketing_opt_in = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_username()


class CustomerAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_addresses",
    )
    label = models.CharField(max_length=80, blank=True)
    recipient_name = models.CharField(max_length=160)
    phone_number = models.CharField(max_length=32)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    region = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=32, blank=True)
    country_code = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(
                r"^[A-Za-z]{2}$",
                "Enter a two-letter country code.",
            )
        ],
    )
    delivery_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="address_user_created_idx",
            )
        ]

    def __str__(self):
        return f"{self.recipient_name} - {self.city}"
