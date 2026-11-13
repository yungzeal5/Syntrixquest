import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    guest_token_hash = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
    )
    contact_email = models.EmailField()
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
    items_subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="orders_user_created_idx",
            ),
            models.Index(
                fields=["status", "created_at"],
                name="orders_status_created_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(items_subtotal__gte=0),
                name="order_subtotal_nonnegative",
            )
        ]

    def __str__(self):
        return str(self.public_id)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    product_name = models.CharField(max_length=200)
    variant_label = models.CharField(max_length=100)
    sku = models.CharField(max_length=64)
    pack_quantity = models.DecimalField(max_digits=12, decimal_places=3)
    pack_unit = models.CharField(max_length=32)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0) & Q(line_total__gte=0),
                name="order_item_amounts_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.sku}"


class StockReservation(models.Model):
    order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.PROTECT,
        related_name="stock_reservation",
    )
    quantity = models.PositiveIntegerField()
    released_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="reservation_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(released_at__isnull=True) | Q(converted_at__isnull=True),
                name="reservation_only_released_or_converted",
            ),
        ]

    def __str__(self):
        return f"Reservation for order item {self.order_item_id}"
