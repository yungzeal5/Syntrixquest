from django.utils import timezone
from rest_framework import serializers

from .models import ProductReview


class PublicProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = (
            "id",
            "display_name",
            "rating",
            "title",
            "body",
            "created_at",
        )
        read_only_fields = fields


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = ("display_name", "rating", "title", "body")
        extra_kwargs = {
            "display_name": {"required": False},
            "title": {"required": False},
        }

    def validate_display_name(self, value):
        return value.strip() or "Customer"

    def validate_body(self, value):
        body = value.strip()
        if not body:
            raise serializers.ValidationError("Review text cannot be blank.")
        return body


class StaffProductReviewSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    moderated_by = serializers.CharField(
        source="moderated_by.username",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = ProductReview
        fields = (
            "id",
            "product",
            "product_name",
            "display_name",
            "rating",
            "title",
            "body",
            "status",
            "moderated_by",
            "moderated_at",
            "created_at",
        )
        read_only_fields = (
            "id",
            "product",
            "product_name",
            "display_name",
            "rating",
            "title",
            "body",
            "moderated_by",
            "moderated_at",
            "created_at",
        )

    def update(self, instance, validated_data):
        new_status = validated_data.get("status", instance.status)
        if new_status != instance.status:
            instance.moderated_by = self.context["request"].user
            instance.moderated_at = timezone.now()
        return super().update(instance, validated_data)
