from rest_framework import serializers

from .models import Order, OrderItem


class CheckoutSerializer(serializers.Serializer):
    contact_email = serializers.EmailField()
    recipient_name = serializers.CharField(max_length=160)
    phone_number = serializers.CharField(max_length=32)
    address_line_1 = serializers.CharField(max_length=255)
    address_line_2 = serializers.CharField(
        max_length=255,
        allow_blank=True,
        required=False,
    )
    city = serializers.CharField(max_length=120)
    region = serializers.CharField(max_length=120)
    postal_code = serializers.CharField(max_length=32, allow_blank=True, required=False)
    country_code = serializers.RegexField(r"^[A-Za-z]{2}$", max_length=2)
    delivery_instructions = serializers.CharField(required=False, allow_blank=True)

    def validate_country_code(self, value):
        return value.upper()


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "product_name",
            "variant_label",
            "sku",
            "pack_quantity",
            "pack_unit",
            "unit_price",
            "quantity",
            "line_total",
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "public_id",
            "status",
            "contact_email",
            "recipient_name",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "city",
            "region",
            "postal_code",
            "country_code",
            "delivery_instructions",
            "items_subtotal",
            "items",
            "paid_at",
            "cancelled_at",
            "created_at",
        )


class StaffOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "product_name",
            "variant_label",
            "sku",
            "quantity",
        )


class StaffOrderQueueSerializer(serializers.ModelSerializer):
    items = StaffOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "public_id",
            "status",
            "created_at",
            "items",
        )
