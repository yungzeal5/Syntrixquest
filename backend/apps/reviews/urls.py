from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProductReviewListCreateView,
    ProductReviewSummaryView,
    StaffProductReviewViewSet,
)

router = DefaultRouter()
router.register("manage", StaffProductReviewViewSet, basename="review-management")

urlpatterns = [
    path(
        "products/<slug:product_slug>/summary/",
        ProductReviewSummaryView.as_view(),
        name="product-review-summary",
    ),
    path(
        "products/<slug:product_slug>/",
        ProductReviewListCreateView.as_view(),
        name="product-reviews",
    ),
    path("", include(router.urls)),
]
