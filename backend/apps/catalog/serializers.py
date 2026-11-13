from rest_framework import serializers

from .models import Category, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "is_active")


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "category",
            "category_id",
            "variants",
        )

    def get_variants(self, product):
        return ProductVariantSerializer(
            product.variants.all(),
            many=True,
            context=self.context,
        ).data


class ProductVariantSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(read_only=True, slug_field="slug")
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True,
    )

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "product",
            "product_id",
            "label",
            "sku",
            "pack_quantity",
            "pack_unit",
            "price",
            "is_active",
            "is_default",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None))
        is_default = attrs.get(
            "is_default",
            getattr(self.instance, "is_default", False),
        )
        if product and is_default:
            defaults = ProductVariant.objects.filter(
                product=product,
                is_default=True,
            )
            if self.instance:
                defaults = defaults.exclude(pk=self.instance.pk)
            if defaults.exists():
                raise serializers.ValidationError(
                    {"is_default": "This product already has a default variant."}
                )
        return attrs

    def create(self, validated_data):
        if (
            "is_default" not in self.initial_data
            and not ProductVariant.objects.filter(
                product=validated_data["product"]
            ).exists()
        ):
            validated_data["is_default"] = True
        return super().create(validated_data)
