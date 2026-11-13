import hashlib
import secrets
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction

from .models import Cart, CartItem

GUEST_CART_COOKIE_NAME = "syntrix_guest_cart"


@dataclass
class CartContext:
    cart: Cart | None
    guest_token: str | None = None
    set_guest_cookie: bool = False
    clear_guest_cookie: bool = False


def hash_guest_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def claim_guest_orders(token_hash, user):
    from apps.orders.models import Order

    return Order.objects.filter(
        guest_token_hash=token_hash,
        user__isnull=True,
    ).update(user=user, guest_token_hash=None)


def attach_guest_cookie(response, context):
    if context.set_guest_cookie:
        response.set_cookie(
            GUEST_CART_COOKIE_NAME,
            context.guest_token,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite="Lax",
            path="/",
        )
    elif context.clear_guest_cookie:
        response.delete_cookie(
            GUEST_CART_COOKIE_NAME,
            samesite="Lax",
            path="/",
        )
    return response


def resolve_cart(request, create=False):
    if request.user.is_authenticated:
        return _resolve_customer_cart(request, create)

    token = request.COOKIES.get(GUEST_CART_COOKIE_NAME)
    if token and len(token) <= 128:
        cart = Cart.objects.filter(guest_token_hash=hash_guest_token(token)).first()
        if cart or not create:
            return CartContext(cart=cart, guest_token=token)
    elif not create:
        return CartContext(cart=None)

    token = secrets.token_urlsafe(32)
    cart = Cart.objects.create(guest_token_hash=hash_guest_token(token))
    return CartContext(cart=cart, guest_token=token, set_guest_cookie=True)


def _resolve_customer_cart(request, create):
    guest_token = request.COOKIES.get(GUEST_CART_COOKIE_NAME)
    clear_guest_cookie = False
    if guest_token and len(guest_token) <= 128:
        token_hash = hash_guest_token(guest_token)
        with transaction.atomic():
            guest_cart = (
                Cart.objects.select_for_update()
                .filter(guest_token_hash=token_hash)
                .first()
            )
            customer_cart = (
                Cart.objects.select_for_update()
                .filter(user=request.user)
                .first()
            )
            if guest_cart:
                if customer_cart is None:
                    guest_cart.user = request.user
                    guest_cart.guest_token_hash = None
                    guest_cart.save(
                        update_fields=["user", "guest_token_hash", "updated_at"]
                    )
                    customer_cart = guest_cart
                else:
                    _merge_items(guest_cart, customer_cart)
                    guest_cart.delete()
                clear_guest_cookie = True

            claimed_orders = claim_guest_orders(token_hash, request.user)
            clear_guest_cookie = clear_guest_cookie or bool(claimed_orders)
            if customer_cart:
                return CartContext(
                    cart=customer_cart,
                    clear_guest_cookie=clear_guest_cookie,
                )

    customer_cart = Cart.objects.filter(user=request.user).first()
    if customer_cart or not create:
        return CartContext(
            cart=customer_cart,
            clear_guest_cookie=clear_guest_cookie,
        )

    return CartContext(
        cart=Cart.objects.create(user=request.user),
        clear_guest_cookie=clear_guest_cookie,
    )


def _merge_items(source, destination):
    for source_item in source.items.select_for_update().order_by("id"):
        destination_item, created = CartItem.objects.get_or_create(
            cart=destination,
            variant=source_item.variant,
            defaults={"quantity": source_item.quantity},
        )
        if not created:
            destination_item.quantity += source_item.quantity
            destination_item.save(update_fields=["quantity", "updated_at"])
