from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import StockBalance, StockMovement
from apps.inventory.services import (
    InsufficientStockError,
    available_quantity,
    record_stock_movement,
)

from .models import Order, StockReservation
from .services import complete_order_payment


class CommerceFlowTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Cups", slug="cups")
        product = Product.objects.create(
            category=category,
            name="Clear Cup",
            slug="clear-cup",
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            label="Pack of 50",
            sku="CUP-050",
            pack_quantity="50",
            pack_unit="pieces",
            price="5.00",
            is_default=True,
        )
        self.balance = StockBalance.objects.get(variant=self.variant)
        self.balance.quantity_on_hand = 10
        self.balance.save(update_fields=["quantity_on_hand"])
        self.client = APIClient()
        self.cart_url = "/api/v1/cart/"
        self.checkout_url = "/api/v1/checkout/"
        self.contact = {
            "contact_email": "guest@example.test",
            "recipient_name": "Guest Customer",
            "phone_number": "555-0100",
            "address_line_1": "1 Main Street",
            "address_line_2": "",
            "city": "Example City",
            "region": "Example Region",
            "postal_code": "12345",
            "country_code": "us",
            "delivery_instructions": "",
        }

    def add_to_cart(self, quantity):
        return self.client.post(
            self.cart_url,
            {"variant_id": self.variant.id, "quantity": quantity},
            format="json",
        )

    def test_empty_guest_cart_has_the_normal_cart_response_shape(self):
        response = self.client.get(self.cart_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"items": [], "items_subtotal": "0.00"})

    def create_guest_order(self, quantity):
        self.assertIn(self.add_to_cart(quantity).status_code, (200, 201))
        return self.client.post(self.checkout_url, self.contact, format="json")

    def test_guest_checkout_reserves_stock_until_cancelled(self):
        add_response = self.add_to_cart(3)

        self.assertEqual(add_response.status_code, 201)
        self.assertTrue(add_response.cookies["syntrix_guest_cart"]["httponly"])
        self.assertNotIn("guest_token", add_response.data)
        self.assertEqual(add_response.data["items"][0]["quantity_available"], 10)
        self.assertEqual(add_response.data["items"][0]["line_total"], "15.00")

        response = self.client.post(self.checkout_url, self.contact, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], Order.Status.PENDING_PAYMENT)
        self.assertEqual(response.data["items_subtotal"], "15.00")
        self.assertEqual(response.data["country_code"], "US")
        self.assertEqual(response.data["items"][0]["unit_price"], "5.00")
        order = Order.objects.get(public_id=response.data["public_id"])
        reservation = StockReservation.objects.get(order_item__order=order)
        self.assertIsNone(reservation.released_at)
        self.assertIsNone(reservation.converted_at)
        self.assertEqual(available_quantity(self.variant.id), 7)
        self.assertEqual(self.client.get(self.cart_url).data["items"], [])
        self.assertEqual(
            self.client.get(f"/api/v1/orders/{order.public_id}/").status_code,
            200,
        )

        other_client = APIClient()
        self.assertEqual(
            other_client.get(f"/api/v1/orders/{order.public_id}/").status_code,
            404,
        )
        cancel_response = self.client.post(
            f"/api/v1/orders/{order.public_id}/cancel/",
            {},
            format="json",
        )

        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(cancel_response.data["status"], Order.Status.CANCELLED)
        self.assertIsNotNone(reservation.__class__.objects.get(pk=reservation.pk).released_at)
        self.assertEqual(available_quantity(self.variant.id), 10)

    def test_payment_conversion_is_idempotent_and_records_sale(self):
        response = self.create_guest_order(2)
        order_id = response.data["public_id"]

        order = complete_order_payment(order_id)
        repeated_order = complete_order_payment(order_id)
        self.balance.refresh_from_db()

        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(repeated_order.status, Order.Status.PAID)
        self.assertEqual(self.balance.quantity_on_hand, 8)
        self.assertEqual(
            StockMovement.objects.filter(
                movement_type=StockMovement.MovementType.SALE,
            ).count(),
            1,
        )
        self.assertEqual(available_quantity(self.variant.id), 8)
        self.assertIsNotNone(
            StockReservation.objects.get(order_item__order=order).converted_at
        )
        self.assertEqual(
            self.client.post(
                f"/api/v1/orders/{order.public_id}/cancel/",
                {},
                format="json",
            ).status_code,
            409,
        )

    def test_checkout_rejects_unavailable_stock_without_clearing_cart(self):
        self.add_to_cart(11)

        response = self.client.post(self.checkout_url, self.contact, format="json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(StockReservation.objects.count(), 0)
        self.assertEqual(len(self.client.get(self.cart_url).data["items"]), 1)
        self.assertEqual(available_quantity(self.variant.id), 10)

    def test_guest_can_update_and_remove_cart_items(self):
        response = self.add_to_cart(1)
        item_id = response.data["items"][0]["id"]

        updated = self.client.patch(
            f"{self.cart_url}items/{item_id}/",
            {"quantity": 4},
            format="json",
        )
        removed = self.client.delete(f"{self.cart_url}items/{item_id}/")

        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["items"][0]["quantity"], 4)
        self.assertEqual(removed.status_code, 204)
        self.assertEqual(self.client.get(self.cart_url).data["items"], [])

    def test_inventory_adjustment_cannot_consume_reserved_stock(self):
        response = self.create_guest_order(5)

        self.assertEqual(response.status_code, 201)
        with self.assertRaises(InsufficientStockError):
            record_stock_movement(
                variant=self.variant,
                movement_type=StockMovement.MovementType.ADJUSTMENT_DECREASE,
                quantity=6,
                reason="Attempt to consume reserved stock",
                user=None,
            )
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity_on_hand, 10)
        self.assertEqual(available_quantity(self.variant.id), 5)

    def test_guest_cart_merges_into_customer_cart_after_login(self):
        self.add_to_cart(2)
        customer = get_user_model().objects.create_user(
            username="returning-customer",
            password="long-safe-password",
        )
        self.client.force_authenticate(user=customer)

        response = self.client.get(self.cart_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["items"][0]["quantity"], 2)
        self.assertEqual(
            response.cookies["syntrix_guest_cart"]["max-age"],
            0,
        )
        self.assertEqual(customer.cart.items.count(), 1)

    def test_guest_order_is_claimed_when_customer_logs_in(self):
        response = self.create_guest_order(2)
        order = Order.objects.get(public_id=response.data["public_id"])
        customer = get_user_model().objects.create_user(
            username="guest-order-owner",
            password="long-safe-password",
        )
        self.client.force_authenticate(user=customer)

        order_response = self.client.get(f"/api/v1/orders/{order.public_id}/")
        self.assertEqual(order_response.status_code, 200)
        order.refresh_from_db()
        self.assertIsNone(order.user)

        cart_response = self.client.get(self.cart_url)
        self.assertEqual(cart_response.cookies["syntrix_guest_cart"]["max-age"], 0)
        order.refresh_from_db()
        self.assertEqual(order.user, customer)
        self.assertIsNone(order.guest_token_hash)
        self.assertEqual(order_response.status_code, 200)
        self.assertEqual(
            self.client.get("/api/v1/orders/").data["count"],
            1,
        )

    def test_catalog_variant_with_order_history_cannot_be_deleted(self):
        order_response = self.create_guest_order(1)
        order = Order.objects.get(public_id=order_response.data["public_id"])
        staff = get_user_model().objects.create_superuser(
            username="catalog-admin",
            password="long-safe-password",
        )
        self.client.force_authenticate(user=staff)

        response = self.client.delete(
            f"/api/v1/catalog/variants/{self.variant.id}/"
        )

        self.assertEqual(response.status_code, 409)
        self.assertTrue(order.items.filter(variant=self.variant).exists())

    def test_order_manager_can_read_sanitized_order_queue(self):
        order_response = self.create_guest_order(2)
        call_command("sync_staff_roles", stdout=StringIO())
        manager = get_user_model().objects.create_user(
            username="order-manager",
            password="long-safe-password",
            is_staff=True,
        )
        manager.groups.add(Group.objects.get(name="Order Manager"))
        self.client.force_authenticate(user=manager)

        response = self.client.get("/api/v1/orders/manage/?page_size=100")

        self.assertEqual(response.status_code, 200)
        result = response.data["results"][0]
        self.assertEqual(result["public_id"], order_response.data["public_id"])
        self.assertEqual(result["status"], Order.Status.PENDING_PAYMENT)
        self.assertEqual(
            result["items"],
            [
                {
                    "product_name": "Clear Cup",
                    "variant_label": "Pack of 50",
                    "sku": "CUP-050",
                    "quantity": 2,
                }
            ],
        )
        for private_or_financial_field in (
            "contact_email",
            "recipient_name",
            "phone_number",
            "address_line_1",
            "items_subtotal",
        ):
            self.assertNotIn(private_or_financial_field, result)

        self.assertEqual(
            self.client.post("/api/v1/orders/manage/", {}, format="json").status_code,
            403,
        )

    def test_order_queue_requires_staff_order_permission(self):
        user = get_user_model().objects.create_user(
            username="unprivileged-staff",
            password="long-safe-password",
            is_staff=True,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/v1/orders/manage/")

        self.assertEqual(response.status_code, 403)

    def test_anonymous_cart_mutation_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        url = "/api/v1/cart/"
        payload = {"variant_id": self.variant.id, "quantity": 1}

        self.assertEqual(client.post(url, payload, format="json").status_code, 403)
        client.get("/api/v1/auth/csrf/")
        csrf_token = client.cookies["csrftoken"].value

        response = client.post(
            url,
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 201)
