from rest_framework import serializers

from apps.catalog.models import ProductVariant
from apps.inventory.services import available_quantity


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.filter(
            is_active=True,
            product__is_active=True,
            product__category__is_active=True,
        ),
        source="variant",
    )
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    variant_id = serializers.IntegerField()
    product_name = serializers.CharField(source="variant.product.name")
    variant_label = serializers.CharField(source="variant.label")
    sku = serializers.CharField(source="variant.sku")
    pack_quantity = serializers.DecimalField(
        source="variant.pack_quantity",
        max_digits=12,
        decimal_places=3,
    )
    pack_unit = serializers.CharField(source="variant.pack_unit")
    unit_price = serializers.DecimalField(
        source="variant.price",
        max_digits=12,
        decimal_places=2,
    )
    quantity = serializers.IntegerField()
    line_total = serializers.SerializerMethodField()
    quantity_available = serializers.SerializerMethodField()

    def get_line_total(self, item):
        return f"{item.variant.price * item.quantity:.2f}"

    def get_quantity_available(self, item):
        return available_quantity(item.variant_id)


class CartSerializer(serializers.Serializer):
    items = serializers.SerializerMethodField()
    items_subtotal = serializers.SerializerMethodField()

    def get_items(self, cart):
        if cart is None:
            return []
        items = cart.items.select_related(
            "variant",
            "variant__product",
        ).order_by("created_at", "id")
        return CartItemSerializer(items, many=True).data

    def get_items_subtotal(self, cart):
        if cart is None:
            return "0.00"
        total = sum(
            (
                item.variant.price * item.quantity
                for item in cart.items.select_related("variant")
            ),
            start=0,
        )
        return f"{total:.2f}"
