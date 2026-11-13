from django.db import transaction
from django.db.models import Sum

from .models import StockBalance, StockMovement


class InsufficientStockError(Exception):
    pass


MOVEMENT_DIRECTIONS = {
    StockMovement.MovementType.RECEIPT: 1,
    StockMovement.MovementType.RETURN: 1,
    StockMovement.MovementType.ADJUSTMENT_INCREASE: 1,
    StockMovement.MovementType.SALE: -1,
    StockMovement.MovementType.DAMAGE: -1,
    StockMovement.MovementType.ADJUSTMENT_DECREASE: -1,
}


def reserved_quantity_for_variant(variant_id):
    from apps.orders.models import StockReservation

    return (
        StockReservation.objects.filter(
            order_item__variant_id=variant_id,
            released_at__isnull=True,
            converted_at__isnull=True,
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )


def available_quantity(variant_id):
    balance = StockBalance.objects.filter(variant_id=variant_id).values_list(
        "quantity_on_hand",
        flat=True,
    ).first()
    return max((balance or 0) - reserved_quantity_for_variant(variant_id), 0)


@transaction.atomic
def record_stock_movement(variant, movement_type, quantity, reason, user):
    if movement_type not in MOVEMENT_DIRECTIONS:
        raise ValueError("Unsupported stock movement type.")
    if quantity <= 0:
        raise ValueError("Stock movement quantity must be greater than zero.")

    balance = StockBalance.objects.select_for_update().get(variant=variant)
    new_quantity = balance.quantity_on_hand + (
        MOVEMENT_DIRECTIONS[movement_type] * quantity
    )
    if new_quantity < 0:
        raise InsufficientStockError(
            "This movement would make the on-hand stock negative."
        )
    if new_quantity < reserved_quantity_for_variant(variant.pk):
        raise InsufficientStockError(
            "This movement would consume stock reserved for pending orders."
        )

    balance.quantity_on_hand = new_quantity
    balance.save(update_fields=["quantity_on_hand", "updated_at"])
    return StockMovement.objects.create(
        variant=variant,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason,
        created_by=user,
    )
