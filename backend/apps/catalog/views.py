from django.db.models import Prefetch
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.core.pagination import StandardPagination
from apps.core.permissions import PublicReadStaffModelPermissions

from .models import Category, Product, ProductVariant
from .serializers import CategorySerializer, ProductSerializer, ProductVariantSerializer


class CatalogConflict(APIException):
    status_code = 409
    default_detail = (
        "This catalog item cannot be deleted while it has stock, cart, "
        "order, or review history."
    )
    default_code = "catalog_conflict"


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [PublicReadStaffModelPermissions]
    lookup_field = "slug"
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = Category.objects.all()
        user = self.request.user
        can_view_inactive = user.is_superuser or (
            user.is_authenticated
            and user.is_staff
            and user.has_perm("catalog.view_category")
        )
        return queryset if can_view_inactive else queryset.filter(is_active=True)


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [PublicReadStaffModelPermissions]
    lookup_field = "slug"
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = Product.objects.select_related("category")
        user = self.request.user
        can_view_inactive = user.is_superuser or (
            user.is_authenticated
            and user.is_staff
            and user.has_perm("catalog.view_product")
        )
        if can_view_inactive:
            can_view_inactive_variants = user.is_superuser or (
                user.is_authenticated
                and user.is_staff
                and user.has_perm("catalog.view_productvariant")
            )
            variant_queryset = (
                ProductVariant.objects.all()
                if can_view_inactive_variants
                else ProductVariant.objects.filter(is_active=True)
            )
            return queryset.prefetch_related(
                Prefetch("variants", queryset=variant_queryset)
            )
        return queryset.filter(
            is_active=True,
            category__is_active=True,
            variants__is_active=True,
        ).prefetch_related(
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True),
            )
        ).distinct()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if (
            instance.variants.filter(stock_movements__isnull=False).exists()
            or instance.variants.filter(cart_items__isnull=False).exists()
            or instance.variants.filter(order_items__isnull=False).exists()
            or instance.reviews.exists()
        ):
            raise CatalogConflict(
                "A product with stock, cart, order, or review history "
                "cannot be deleted. "
                "Deactivate it instead."
            )
        instance.delete()
        return Response(status=204)


class ProductVariantViewSet(ModelViewSet):
    serializer_class = ProductVariantSerializer
    permission_classes = [PublicReadStaffModelPermissions]
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = ProductVariant.objects.select_related("product", "product__category")
        user = self.request.user
        can_view_inactive = user.is_superuser or (
            user.is_authenticated
            and user.is_staff
            and user.has_perm("catalog.view_productvariant")
        )
        if can_view_inactive:
            return queryset
        return queryset.filter(
            is_active=True,
            product__is_active=True,
            product__category__is_active=True,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if (
            instance.stock_movements.exists()
            or instance.cart_items.exists()
            or instance.order_items.exists()
        ):
            raise CatalogConflict(
                "A variant with stock, cart, or order history cannot be deleted. "
                "Deactivate it instead."
            )
        instance.delete()
        return Response(status=204)
