from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class StockBalance(models.Model):
    variant = models.OneToOneField(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="stock_balance",
    )
    quantity_on_hand = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["variant_id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity_on_hand__gte=0),
                name="inventory_balance_nonnegative",
            )
        ]

    def __str__(self):
        return f"{self.variant.sku}: {self.quantity_on_hand}"


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        RECEIPT = "receipt", "Receipt"
        RETURN = "return", "Return"
        SALE = "sale", "Sale"
        DAMAGE = "damage", "Damage"
        ADJUSTMENT_INCREASE = "adjustment_increase", "Adjustment increase"
        ADJUSTMENT_DECREASE = "adjustment_decrease", "Adjustment decrease"

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    movement_type = models.CharField(max_length=24, choices=MovementType.choices)
    quantity = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    reason = models.CharField(max_length=500)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["variant", "created_at"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="inventory_movement_quantity_positive",
            )
        ]

    def __str__(self):
        return (
            f"{self.get_movement_type_display()} {self.quantity} "
            f"of {self.variant.sku}"
        )
