from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.catalog.models import Product
from apps.core.pagination import StandardPagination
from apps.core.permissions import StaffModelPermissions

from .models import ProductReview
from .serializers import (
    ProductReviewCreateSerializer,
    PublicProductReviewSerializer,
    StaffProductReviewSerializer,
)


class ProductReviewListCreateView(generics.ListCreateAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    pagination_class = StandardPagination
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "review_submit"

    def get_throttles(self):
        if self.request.method == "POST":
            return super().get_throttles()
        return []

    def get_product(self):
        return get_object_or_404(
            Product,
            slug=self.kwargs["product_slug"],
            is_active=True,
            category__is_active=True,
        )

    def get_queryset(self):
        return ProductReview.objects.filter(
            product=self.get_product(),
            status=ProductReview.Status.APPROVED,
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductReviewCreateSerializer
        return PublicProductReviewSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(
            product=self.get_product(),
            user=user if user.is_authenticated else None,
        )


class ProductReviewSummaryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, product_slug):
        product = get_object_or_404(
            Product,
            slug=product_slug,
            is_active=True,
            category__is_active=True,
        )
        summary = ProductReview.objects.filter(
            product=product,
            status=ProductReview.Status.APPROVED,
        ).aggregate(average=Avg("rating"), count=Count("id"))
        return Response(
            {
                "average_rating": f"{summary['average'] or 0:.1f}",
                "review_count": summary["count"],
            }
        )


class StaffProductReviewViewSet(ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [StaffModelPermissions]
    serializer_class = StaffProductReviewSerializer
    pagination_class = StandardPagination
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return ProductReview.objects.select_related(
            "product",
            "moderated_by",
        ).all()
