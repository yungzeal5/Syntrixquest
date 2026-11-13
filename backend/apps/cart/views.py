from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import ProductVariant

from .models import Cart, CartItem
from .serializers import (
    AddCartItemSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)
from .services import (
    attach_guest_cookie,
    resolve_cart,
)


@method_decorator(csrf_protect, name="dispatch")
class CartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        context = resolve_cart(request)
        data = (
            CartSerializer(context.cart).data
            if context.cart is not None
            else {"items": [], "items_subtotal": "0.00"}
        )
        response = Response(data)
        return attach_guest_cookie(response, context)

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = serializer.validated_data["variant"]
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().get(pk=variant.pk)
            if not (
                variant.is_active
                and variant.product.is_active
                and variant.product.category.is_active
            ):
                raise ValidationError({"variant_id": "This variant is not available."})
            context = resolve_cart(request, create=True)
            cart = Cart.objects.select_for_update().get(pk=context.cart.pk)
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                variant=variant,
                defaults={"quantity": quantity},
            )
            if not created:
                item.quantity += quantity
                item.save(update_fields=["quantity", "updated_at"])

        response = Response(
            CartSerializer(context.cart).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
        return attach_guest_cookie(response, context)


@method_decorator(csrf_protect, name="dispatch")
class CartItemDetailView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, pk):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        context = resolve_cart(request)
        if context.cart is None:
            raise NotFound("The cart item does not exist.")
        try:
            with transaction.atomic():
                item = CartItem.objects.select_for_update().get(
                    cart=context.cart,
                    pk=pk,
                )
                item.quantity = serializer.validated_data["quantity"]
                item.save(update_fields=["quantity", "updated_at"])
        except CartItem.DoesNotExist as exc:
            raise NotFound("The cart item does not exist.") from exc

        response = Response(CartSerializer(context.cart).data)
        return attach_guest_cookie(response, context)

    def delete(self, request, pk):
        context = resolve_cart(request)
        if context.cart is None:
            raise NotFound("The cart item does not exist.")
        deleted, _ = CartItem.objects.filter(cart=context.cart, pk=pk).delete()
        if not deleted:
            raise NotFound("The cart item does not exist.")
        response = Response(status=status.HTTP_204_NO_CONTENT)
        return attach_guest_cookie(response, context)
