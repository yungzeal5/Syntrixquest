from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.inventory.models import StockBalance, StockMovement
from apps.orders.models import Order, OrderItem

from .models import Category, Product, ProductVariant


class ProductApiTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Cups", slug="cups")
        product = Product.objects.create(
            category=category,
            name="Clear Cup",
            slug="clear-cup",
        )
        ProductVariant.objects.create(
            product=product,
            label="Pack of 50",
            sku="CUP-001",
            pack_quantity=Decimal("50"),
            pack_unit="pieces",
            price=Decimal("5.00"),
            is_default=True,
        )

    def test_public_catalogue_lists_active_products(self):
        response = APIClient().get("/api/v1/catalog/products/")

        self.assertEqual(response.status_code, 200)
        product = response.data["results"][0]
        self.assertEqual(product["slug"], "clear-cup")
        self.assertEqual(product["variants"][0]["sku"], "CUP-001")
        self.assertEqual(product["variants"][0]["pack_unit"], "pieces")
        self.assertNotIn("price", product)

    def test_catalogue_supports_client_sized_pages(self):
        response = APIClient().get("/api/v1/catalog/products/?page_size=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)


class DemoCatalogCommandTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Real Category", slug="real-category")
        self.product = Product.objects.create(
            category=category,
            name="Real Product",
            slug="real-product",
        )
        self.real_variant = ProductVariant.objects.create(
            product=self.product,
            label="Single",
            sku="REAL-BASE-001",
            price=Decimal("1.00"),
        )

    def test_seed_is_idempotent_and_clear_removes_only_demo_rows(self):
        call_command("seed_demo_catalog", stdout=StringIO())
        initial_stock = list(
            StockBalance.objects.filter(variant__sku__startswith="DEMO-")
            .order_by("variant_id")
            .values_list("quantity_on_hand", flat=True)
        )
        self.assertEqual(initial_stock, [40, 20, 30, 12, 35, 45])
        StockBalance.objects.filter(variant__sku="DEMO-CUP-050").update(
            quantity_on_hand=7
        )
        expected_stock = list(
            StockBalance.objects.filter(variant__sku__startswith="DEMO-")
            .order_by("variant_id")
            .values_list("quantity_on_hand", flat=True)
        )

        call_command("seed_demo_catalog", stdout=StringIO())

        self.assertEqual(
            Product.objects.filter(slug__startswith="demo-").count(),
            4,
        )
        self.assertEqual(
            ProductVariant.objects.filter(sku__startswith="DEMO-").count(),
            6,
        )
        self.assertEqual(
            StockMovement.objects.filter(variant__sku__startswith="DEMO-").count(),
            6,
        )
        self.assertEqual(
            list(
                StockBalance.objects.filter(variant__sku__startswith="DEMO-")
                .order_by("variant_id")
                .values_list("quantity_on_hand", flat=True)
            ),
            expected_stock,
        )

        with self.assertRaises(CommandError):
            call_command("clear_demo_catalog", stdout=StringIO())
        call_command("clear_demo_catalog", confirm=True, stdout=StringIO())

        self.assertEqual(
            ProductVariant.objects.filter(sku__startswith="DEMO-").count(),
            0,
        )
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
        self.assertTrue(
            ProductVariant.objects.filter(pk=self.real_variant.pk).exists()
        )
        self.assertTrue(
            Category.objects.filter(slug="real-category").exists()
        )

    def test_clear_refuses_mixed_orders_and_preserves_demo_data(self):
        call_command("seed_demo_catalog", stdout=StringIO())
        demo_variant = ProductVariant.objects.get(sku="DEMO-CUP-050")
        real_variant = self.real_variant
        order = Order.objects.create(
            contact_email="test@example.com",
            recipient_name="Test Customer",
            phone_number="555-0100",
            address_line_1="1 Test Street",
            city="Test City",
            region="Test Region",
            country_code="US",
            items_subtotal=Decimal("8.50"),
        )
        for variant in (demo_variant, real_variant):
            OrderItem.objects.create(
                order=order,
                variant=variant,
                product_name=variant.product.name,
                variant_label=variant.label,
                sku=variant.sku,
                pack_quantity=Decimal("1"),
                pack_unit="each",
                unit_price=variant.price,
                quantity=1,
                line_total=variant.price,
            )

        with self.assertRaises(CommandError):
            call_command("clear_demo_catalog", confirm=True, stdout=StringIO())

        self.assertTrue(ProductVariant.objects.filter(pk=demo_variant.pk).exists())
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())

    def test_clear_refuses_paid_demo_orders(self):
        call_command("seed_demo_catalog", stdout=StringIO())
        demo_variant = ProductVariant.objects.get(sku="DEMO-CUP-050")
        order = Order.objects.create(
            status=Order.Status.PAID,
            contact_email="test@example.com",
            recipient_name="Test Customer",
            phone_number="555-0100",
            address_line_1="1 Test Street",
            city="Test City",
            region="Test Region",
            country_code="US",
            items_subtotal=Decimal("7.50"),
        )
        OrderItem.objects.create(
            order=order,
            variant=demo_variant,
            product_name=demo_variant.product.name,
            variant_label=demo_variant.label,
            sku=demo_variant.sku,
            pack_quantity=demo_variant.pack_quantity,
            pack_unit=demo_variant.pack_unit,
            unit_price=demo_variant.price,
            quantity=1,
            line_total=demo_variant.price,
        )

        with self.assertRaises(CommandError):
            call_command("clear_demo_catalog", confirm=True, stdout=StringIO())

        self.assertTrue(ProductVariant.objects.filter(pk=demo_variant.pk).exists())
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())


class StaffCatalogPermissionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalog-staff",
            password="Safe-Long-Password-984!",
            is_staff=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.categories_url = "/api/v1/catalog/categories/"
        self.category = Category.objects.create(name="Cups", slug="cups")
        self.product = Product.objects.create(
            category=self.category,
            name="Catalog Test Product",
            slug="catalog-test-product",
        )

    def test_staff_without_a_catalog_role_cannot_write(self):
        response = self.client.post(
            self.categories_url,
            {"name": "New Category", "slug": "new-category"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_without_a_catalog_role_cannot_view_inactive_categories(self):
        inactive = Category.objects.create(
            name="Inactive",
            slug="inactive",
            is_active=False,
        )

        response = self.client.get(self.categories_url)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            inactive.id,
            [item["id"] for item in response.data["results"]],
        )

    def test_store_manager_can_write_catalog_and_view_inactive_categories(self):
        call_command("sync_staff_roles", stdout=StringIO())
        self.user.groups.add(Group.objects.get(name="Store Manager"))
        inactive = Category.objects.create(
            name="Inactive",
            slug="inactive",
            is_active=False,
        )
        list_response = self.client.get(self.categories_url)
        create_response = self.client.post(
            self.categories_url,
            {"name": "New Category", "slug": "new-category"},
            format="json",
        )
        product_response = self.client.post(
            "/api/v1/catalog/products/",
            {
                "name": "New Cup",
                "slug": "new-cup",
                "category_id": self.category.id,
            },
            format="json",
        )
        variant_response = self.client.post(
            "/api/v1/catalog/variants/",
            {
                "product_id": product_response.data["id"],
                "label": "Pack of 100",
                "sku": "CUP-002",
                "pack_quantity": "100",
                "pack_unit": "pieces",
                "price": "6.00",
            },
            format="json",
        )

        self.assertIn(
            inactive.id,
            [item["id"] for item in list_response.data["results"]],
        )
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(product_response.status_code, 201)
        self.assertEqual(variant_response.status_code, 201)

    def test_staff_without_catalog_role_cannot_create_variants(self):
        response = self.client.post(
            "/api/v1/catalog/variants/",
            {
                "product_id": self.product.id,
                "label": "Pack",
                "sku": "CUP-003",
                "price": "5.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_store_manager_group_does_not_grant_access_without_staff_flag(self):
        call_command("sync_staff_roles", stdout=StringIO())
        self.user.is_staff = False
        self.user.save(update_fields=["is_staff"])
        self.user.groups.add(Group.objects.get(name="Store Manager"))

        response = self.client.post(
            self.categories_url,
            {"name": "New Category", "slug": "new-category"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_write_catalog(self):
        self.user.is_superuser = True
        self.user.save(update_fields=["is_superuser"])

        response = self.client.post(
            self.categories_url,
            {"name": "New Category", "slug": "new-category"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
