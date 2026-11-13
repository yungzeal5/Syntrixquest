from django.db.models import Avg, Count, Q, Sum
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Product, ProductVariant
from apps.feedback.models import CustomerFeedback
from apps.inventory.models import StockBalance
from apps.orders.models import Order, StockReservation
from apps.reviews.models import ProductReview


class OperationsOverviewView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        on_hand = (
            StockBalance.objects.aggregate(total=Sum("quantity_on_hand"))["total"]
            or 0
        )
        reserved = (
            StockReservation.objects.filter(
                released_at__isnull=True,
                converted_at__isnull=True,
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        review_metrics = ProductReview.objects.aggregate(
            pending=Count("id", filter=Q(status=ProductReview.Status.PENDING)),
            approved=Count("id", filter=Q(status=ProductReview.Status.APPROVED)),
            rejected=Count("id", filter=Q(status=ProductReview.Status.REJECTED)),
            average_rating=Avg(
                "rating",
                filter=Q(status=ProductReview.Status.APPROVED),
            ),
        )

        return Response(
            {
                "catalog": {
                    "active_products": Product.objects.filter(
                        is_active=True,
                        category__is_active=True,
                    ).count(),
                    "active_variants": ProductVariant.objects.filter(
                        is_active=True,
                        product__is_active=True,
                        product__category__is_active=True,
                    ).count(),
                },
                "inventory": {
                    "packages_on_hand": on_hand,
                    "packages_reserved": reserved,
                    "packages_available": on_hand - reserved,
                },
                "orders": {
                    status: Order.objects.filter(status=status).count()
                    for status, _ in Order.Status.choices
                },
                "reviews": {
                    "pending": review_metrics["pending"],
                    "approved": review_metrics["approved"],
                    "rejected": review_metrics["rejected"],
                    "average_approved_rating": (
                        f"{review_metrics['average_rating']:.1f}"
                        if review_metrics["average_rating"] is not None
                        else "0.0"
                    ),
                },
                "feedback": {
                    status: CustomerFeedback.objects.filter(status=status).count()
                    for status, _ in CustomerFeedback.Status.choices
                },
            }
        )
