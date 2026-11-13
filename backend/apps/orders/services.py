from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.catalog.models import ProductVariant
from apps.inventory.models import StockBalance, StockMovement
from apps.inventory.services import (
    InsufficientStockError,
    record_stock_movement,
    reserved_quantity_for_variant,
)

from .models import Order, OrderItem, StockReservation


class EmptyCartError(Exception):
    pass


class OutOfStockError(Exception):
    pass


class OrderStateError(Exception):
    pass


@transaction.atomic
def create_order_from_cart(cart, contact, user, guest_token_hash):
    cart = Cart.objects.select_for_update().get(pk=cart.pk)
    cart_items = list(
        CartItem.objects.filter(cart=cart)
        .select_related("variant")
        .order_by("variant_id")
    )
    if not cart_items:
        raise EmptyCartError("Your cart is empty.")

    variant_ids = [item.variant_id for item in cart_items]
    variants = list(
        ProductVariant.objects.select_for_update()
        .select_related("product", "product__category")
        .filter(pk__in=variant_ids)
        .order_by("pk")
    )
    variants_by_id = {variant.pk: variant for variant in variants}
    for item in cart_items:
        variant = variants_by_id.get(item.variant_id)
        if (
            variant is None
            or not variant.is_active
            or not variant.product.is_active
            or not variant.product.category.is_active
        ):
            raise OutOfStockError(
                f"{item.variant.sku} is no longer available. Remove it from your cart."
            )

    for variant_id in variant_ids:
        StockBalance.objects.get_or_create(variant_id=variant_id)
    balances = list(
        StockBalance.objects.select_for_update()
        .filter(variant_id__in=variant_ids)
        .order_by("variant_id")
    )
    balances_by_variant = {balance.variant_id: balance for balance in balances}
    for item in cart_items:
        balance = balances_by_variant[item.variant_id]
        available = balance.quantity_on_hand - reserved_quantity_for_variant(
            item.variant_id
        )
        if item.quantity > available:
            raise OutOfStockError(
                f"Only {max(available, 0)} packages of {item.variant.sku} "
                "are currently available."
            )

    subtotal = sum(
        (
            variants_by_id[item.variant_id].price * item.quantity
            for item in cart_items
        ),
        start=Decimal("0.00"),
    )
    order = Order.objects.create(
        user=user if user and user.is_authenticated else None,
        guest_token_hash=(
            guest_token_hash
            if not user or not user.is_authenticated
            else None
        ),
        items_subtotal=subtotal,
        **contact,
    )
    for cart_item in cart_items:
        variant = variants_by_id[cart_item.variant_id]
        order_item = OrderItem.objects.create(
            order=order,
            variant=variant,
            product_name=variant.product.name,
            variant_label=variant.label,
            sku=variant.sku,
            pack_quantity=variant.pack_quantity,
            pack_unit=variant.pack_unit,
            unit_price=variant.price,
            quantity=cart_item.quantity,
            line_total=variant.price * cart_item.quantity,
        )
        StockReservation.objects.create(
            order_item=order_item,
            quantity=cart_item.quantity,
        )
    CartItem.objects.filter(cart=cart).delete()
    return order


@transaction.atomic
def cancel_order(public_id):
    order = Order.objects.select_for_update().get(public_id=public_id)
    if order.status == Order.Status.CANCELLED:
        return order
    if order.status != Order.Status.PENDING_PAYMENT:
        raise OrderStateError("Only unpaid orders can be cancelled.")

    reservations = list(
        StockReservation.objects.select_related("order_item")
        .filter(
            order_item__order=order,
            released_at__isnull=True,
            converted_at__isnull=True,
        )
        .order_by("order_item__variant_id")
    )
    variant_ids = [reservation.order_item.variant_id for reservation in reservations]
    list(
        StockBalance.objects.select_for_update()
        .filter(variant_id__in=variant_ids)
        .order_by("variant_id")
    )
    now = timezone.now()
    for reservation in reservations:
        reservation.released_at = now
        reservation.save(update_fields=["released_at"])
    order.status = Order.Status.CANCELLED
    order.cancelled_at = now
    order.save(update_fields=["status", "cancelled_at", "updated_at"])
    return order


@transaction.atomic
def complete_order_payment(public_id):
    order = Order.objects.select_for_update().get(public_id=public_id)
    if order.status == Order.Status.PAID:
        return order
    if order.status != Order.Status.PENDING_PAYMENT:
        raise OrderStateError("Only pending orders can be marked paid.")

    reservations = list(
        StockReservation.objects.select_related("order_item__variant")
        .filter(
            order_item__order=order,
            released_at__isnull=True,
            converted_at__isnull=True,
        )
        .order_by("order_item__variant_id")
    )
    if not reservations:
        raise OrderStateError("The order has no active stock reservations.")

    variant_ids = [reservation.order_item.variant_id for reservation in reservations]
    list(
        StockBalance.objects.select_for_update()
        .filter(variant_id__in=variant_ids)
        .order_by("variant_id")
    )
    now = timezone.now()
    for reservation in reservations:
        reservation.converted_at = now
        reservation.save(update_fields=["converted_at"])
    try:
        for reservation in reservations:
            order_item = reservation.order_item
            record_stock_movement(
                variant=order_item.variant,
                movement_type=StockMovement.MovementType.SALE,
                quantity=reservation.quantity,
                reason=f"Paid order {order.public_id}",
                user=None,
            )
    except InsufficientStockError as exc:
        raise OrderStateError(
            "The reserved stock could not be converted to a sale."
        ) from exc

    order.status = Order.Status.PAID
    order.paid_at = now
    order.save(update_fields=["status", "paid_at", "updated_at"])
    return order
