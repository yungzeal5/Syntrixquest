from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import StockMovement
from apps.inventory.services import record_stock_movement

DEMO_CATEGORIES = (
    ("demo-disposables", "Demo Disposables"),
    ("demo-takeaway", "Demo Takeaway Packaging"),
    ("demo-cleaning", "Demo Cleaning Supplies"),
)

DEMO_PRODUCTS = (
    {
        "category_slug": "demo-disposables",
        "slug": "demo-paper-cups",
        "name": "Demo Paper Cups",
        "description": "Mock product for local storefront and cart testing.",
        "variants": (
            {
                "label": "Pack of 50",
                "sku": "DEMO-CUP-050",
                "pack_quantity": Decimal("50"),
                "pack_unit": "pieces",
                "price": Decimal("7.50"),
                "stock": 40,
                "is_default": True,
            },
            {
                "label": "Pack of 100",
                "sku": "DEMO-CUP-100",
                "pack_quantity": Decimal("100"),
                "pack_unit": "pieces",
                "price": Decimal("13.00"),
                "stock": 20,
                "is_default": False,
            },
        ),
    },
    {
        "category_slug": "demo-takeaway",
        "slug": "demo-food-containers",
        "name": "Demo Food Containers",
        "description": "Mock product for local storefront and cart testing.",
        "variants": (
            {
                "label": "Pack of 25",
                "sku": "DEMO-BOX-025",
                "pack_quantity": Decimal("25"),
                "pack_unit": "pieces",
                "price": Decimal("8.00"),
                "stock": 30,
                "is_default": True,
            },
            {
                "label": "Pack of 100",
                "sku": "DEMO-BOX-100",
                "pack_quantity": Decimal("100"),
                "pack_unit": "pieces",
                "price": Decimal("24.00"),
                "stock": 12,
                "is_default": False,
            },
        ),
    },
    {
        "category_slug": "demo-takeaway",
        "slug": "demo-kraft-bags",
        "name": "Demo Kraft Paper Bags",
        "description": "Mock product for local storefront and cart testing.",
        "variants": (
            {
                "label": "Pack of 50",
                "sku": "DEMO-BAG-050",
                "pack_quantity": Decimal("50"),
                "pack_unit": "pieces",
                "price": Decimal("5.50"),
                "stock": 35,
                "is_default": True,
            },
        ),
    },
    {
        "category_slug": "demo-cleaning",
        "slug": "demo-cleaning-cloths",
        "name": "Demo Cleaning Cloths",
        "description": "Mock product for local storefront and cart testing.",
        "variants": (
            {
                "label": "Pack of 10",
                "sku": "DEMO-CLOTH-010",
                "pack_quantity": Decimal("10"),
                "pack_unit": "pieces",
                "price": Decimal("4.75"),
                "stock": 45,
                "is_default": True,
            },
        ),
    },
)


class Command(BaseCommand):
    help = "Add clearly labeled mock products and stock for local UI testing."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        created_categories = 0
        created_products = 0
        created_variants = 0

        for slug, name in DEMO_CATEGORIES:
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": "Mock catalog data for local testing.",
                },
            )
            if category.name != name:
                raise CommandError(f"Existing category {slug!r} has a different name.")
            categories[slug] = category
            created_categories += int(created)

        for product_data in DEMO_PRODUCTS:
            product, created = Product.objects.get_or_create(
                slug=product_data["slug"],
                defaults={
                    "category": categories[product_data["category_slug"]],
                    "name": product_data["name"],
                    "description": product_data["description"],
                },
            )
            if (
                product.name != product_data["name"]
                or product.category_id
                != categories[product_data["category_slug"]].id
            ):
                raise CommandError(
                    f"Existing product {product_data['slug']!r} "
                    "does not match demo data."
                )
            created_products += int(created)

            for variant_data in product_data["variants"]:
                variant, variant_created = ProductVariant.objects.get_or_create(
                    sku=variant_data["sku"],
                    defaults={
                        "product": product,
                        "label": variant_data["label"],
                        "pack_quantity": variant_data["pack_quantity"],
                        "pack_unit": variant_data["pack_unit"],
                        "price": variant_data["price"],
                        "is_default": variant_data["is_default"],
                    },
                )
                expected = (
                    product.id,
                    variant_data["label"],
                    variant_data["pack_quantity"],
                    variant_data["pack_unit"],
                    variant_data["price"],
                    variant_data["is_default"],
                )
                actual = (
                    variant.product_id,
                    variant.label,
                    variant.pack_quantity,
                    variant.pack_unit,
                    variant.price,
                    variant.is_default,
                )
                if actual != expected:
                    raise CommandError(
                        f"Existing variant {variant_data['sku']!r} "
                        "does not match demo data."
                    )
                if variant_created:
                    record_stock_movement(
                        variant=variant,
                        movement_type=StockMovement.MovementType.RECEIPT,
                        quantity=variant_data["stock"],
                        reason="Mock inventory for local UI testing",
                        user=None,
                    )
                    created_variants += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Demo catalog ready: "
                f"{created_categories} categories, {created_products} products, "
                f"{created_variants} variants with opening stock added. "
                "Existing demo records were left unchanged."
            )
        )
