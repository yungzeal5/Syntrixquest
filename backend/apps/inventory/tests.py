from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductVariant

from .models import StockBalance, StockMovement


class StockManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="inventory-manager",
            password="Safe-Long-Password-984!",
            is_staff=True,
        )
        call_command("sync_staff_roles", stdout=StringIO())
        self.user.groups.add(Group.objects.get(name="Store Manager"))
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
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.balances_url = "/api/v1/inventory/balances/"
        self.movements_url = "/api/v1/inventory/movements/"

    def post_movement(self, movement_type, quantity):
        return self.client.post(
            self.movements_url,
            {
                "variant_id": self.variant.id,
                "movement_type": movement_type,
                "quantity": quantity,
                "reason": "Inventory test",
            },
            format="json",
        )

    def test_receipts_and_adjustments_update_balance_and_keep_ledger(self):
        receipt = self.post_movement("receipt", 12)
        adjustment = self.post_movement("adjustment_decrease", 3)

        self.assertEqual(receipt.status_code, 201)
        self.assertEqual(adjustment.status_code, 201)
        self.assertEqual(adjustment.data["created_by"], self.user.username)
        balance_response = self.client.get(self.balances_url)
        self.assertEqual(
            balance_response.data["results"][0]["quantity_on_hand"],
            9,
        )
        self.assertEqual(StockMovement.objects.count(), 2)

    def test_movement_that_would_make_stock_negative_is_rejected(self):
        response = self.post_movement("sale", 1)

        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", response.data)
        self.assertEqual(
            StockBalance.objects.get(variant=self.variant).quantity_on_hand,
            0,
        )
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_stock_is_private_to_staff_with_the_inventory_role(self):
        unassigned_staff = get_user_model().objects.create_user(
            username="unassigned-staff",
            is_staff=True,
        )
        client = APIClient()
        client.force_authenticate(user=unassigned_staff)

        self.assertEqual(client.get(self.balances_url).status_code, 403)
        self.assertEqual(
            client.get(self.movements_url).status_code,
            403,
        )
        self.assertEqual(
            client.post(
                self.movements_url,
                {
                    "variant_id": self.variant.id,
                    "movement_type": "receipt",
                    "quantity": 1,
                    "reason": "Unauthorized attempt",
                },
                format="json",
            ).status_code,
            403,
        )

    def test_movement_ledger_cannot_be_edited_or_deleted(self):
        response = self.post_movement("receipt", 4)
        movement_url = f"{self.movements_url}{response.data['id']}/"

        self.assertEqual(
            self.client.patch(
                movement_url,
                {"quantity": 1},
                format="json",
            ).status_code,
            404,
        )
        self.assertEqual(self.client.delete(movement_url).status_code, 404)
