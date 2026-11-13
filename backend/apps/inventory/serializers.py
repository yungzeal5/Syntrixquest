from rest_framework import serializers

from apps.catalog.models import ProductVariant

from .models import StockBalance, StockMovement
from .services import (
    InsufficientStockError,
    record_stock_movement,
    reserved_quantity_for_variant,
)


class StockBalanceSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField(read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    variant_label = serializers.CharField(source="variant.label", read_only=True)
    quantity_reserved = serializers.SerializerMethodField()
    quantity_available = serializers.SerializerMethodField()

    class Meta:
        model = StockBalance
        fields = (
            "variant_id",
            "sku",
            "product_name",
            "variant_label",
            "quantity_on_hand",
            "quantity_reserved",
            "quantity_available",
            "updated_at",
        )

    def get_quantity_reserved(self, balance):
        return reserved_quantity_for_variant(balance.variant_id)

    def get_quantity_available(self, balance):
        return max(
            balance.quantity_on_hand - self.get_quantity_reserved(balance),
            0,
        )


class StockMovementSerializer(serializers.ModelSerializer):
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        source="variant",
    )
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)
    created_by = serializers.CharField(
        source="created_by.username",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = StockMovement
        fields = (
            "id",
            "variant_id",
            "variant_sku",
            "movement_type",
            "quantity",
            "reason",
            "created_by",
            "created_at",
        )
        read_only_fields = ("id", "created_by", "created_at")

    def create(self, validated_data):
        try:
            return record_stock_movement(
                variant=validated_data["variant"],
                movement_type=validated_data["movement_type"],
                quantity=validated_data["quantity"],
                reason=validated_data["reason"],
                user=self.context["request"].user,
            )
        except InsufficientStockError as exc:
            raise serializers.ValidationError({"quantity": str(exc)}) from exc
