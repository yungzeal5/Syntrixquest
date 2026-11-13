from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductVariant
from apps.feedback.models import CustomerFeedback
from apps.inventory.models import StockBalance
from apps.orders.models import Order, OrderItem, StockReservation
from apps.reviews.models import ProductReview


class OperationsOverviewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Supplies", slug="supplies")
        self.product = Product.objects.create(
            category=category,
            name="Sample Product",
            slug="sample-product",
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            label="Pack of 10",
            sku="SAMPLE-010",
            pack_quantity="10",
            pack_unit="pieces",
            price="4.00",
            is_default=True,
        )
        self.balance = StockBalance.objects.get(variant=self.variant)
        self.balance.quantity_on_hand = 12
        self.balance.save(update_fields=["quantity_on_hand"])
        self.client = APIClient()

    def create_order(self, status, quantity=1):
        order = Order.objects.create(
            status=status,
            contact_email="customer@example.test",
            recipient_name="Test Customer",
            phone_number="555-0100",
            address_line_1="1 Test Street",
            city="Test City",
            region="Test Region",
            country_code="US",
            items_subtotal="4.00",
        )
        item = OrderItem.objects.create(
            order=order,
            variant=self.variant,
            product_name=self.product.name,
            variant_label=self.variant.label,
            sku=self.variant.sku,
            pack_quantity=self.variant.pack_quantity,
            pack_unit=self.variant.pack_unit,
            unit_price=self.variant.price,
            quantity=quantity,
            line_total=Decimal("4.00") * quantity,
        )
        return order, item

    def test_staff_overview_reports_operational_counts_without_money(self):
        _order, item = self.create_order(
            Order.Status.PENDING_PAYMENT,
            quantity=3,
        )
        self.create_order(Order.Status.CANCELLED)
        StockReservation.objects.create(order_item=item, quantity=3)
        ProductReview.objects.create(
            product=self.product,
            rating=5,
            body="Looks good.",
            status=ProductReview.Status.APPROVED,
        )
        ProductReview.objects.create(
            product=self.product,
            rating=2,
            body="Awaiting review.",
            status=ProductReview.Status.PENDING,
        )
        CustomerFeedback.objects.create(
            category=CustomerFeedback.Category.WEBSITE,
            message="The catalog works well.",
        )
        staff_user = get_user_model().objects.create_user(
            username="staff",
            password="long-safe-password",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff_user)

        response = self.client.get("/api/v1/analytics/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "catalog": {"active_products": 1, "active_variants": 1},
                "inventory": {
                    "packages_on_hand": 12,
                    "packages_reserved": 3,
                    "packages_available": 9,
                },
                "orders": {
                    Order.Status.PENDING_PAYMENT: 1,
                    Order.Status.PAID: 0,
                    Order.Status.CANCELLED: 1,
                },
                "reviews": {
                    "pending": 1,
                    "approved": 1,
                    "rejected": 0,
                    "average_approved_rating": "5.0",
                },
                "feedback": {
                    CustomerFeedback.Status.NEW: 1,
                    CustomerFeedback.Status.IN_PROGRESS: 0,
                    CustomerFeedback.Status.RESOLVED: 0,
                },
            },
        )
        self.assertNotIn("revenue", response.data)
        self.assertNotIn("items_subtotal", str(response.data))

    def test_non_staff_cannot_access_overview(self):
        response = self.client.get("/api/v1/analytics/overview/")

        self.assertEqual(response.status_code, 403)
