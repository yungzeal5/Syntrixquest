from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.cart.models import CartItem
from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import StockMovement
from apps.orders.models import Order, OrderItem, StockReservation

DEMO_SKU_PREFIX = "DEMO-"
DEMO_PRODUCT_SLUGS = (
    "demo-paper-cups",
    "demo-food-containers",
    "demo-kraft-bags",
    "demo-cleaning-cloths",
)
DEMO_CATEGORY_SLUGS = (
    "demo-disposables",
    "demo-takeaway",
    "demo-cleaning",
)


class Command(BaseCommand):
    help = (
        "Permanently remove demo catalog data and demo-only test orders. "
        "Requires --confirm."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help=(
                "Confirm deletion of demo catalog, stock history, "
                "and demo-only orders."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError(
                "This command deletes mock data. Re-run with --confirm to proceed."
            )

        demo_products = Product.objects.filter(slug__in=DEMO_PRODUCT_SLUGS)
        variants = ProductVariant.objects.filter(
            sku__startswith=DEMO_SKU_PREFIX,
            product__in=demo_products,
        )
        variant_ids = list(variants.values_list("id", flat=True))
        demo_order_ids = list(
            OrderItem.objects.filter(variant_id__in=variant_ids)
            .values_list("order_id", flat=True)
            .distinct()
        )
        demo_orders = Order.objects.filter(id__in=demo_order_ids)
        if demo_orders.filter(status=Order.Status.PAID).exists():
            raise CommandError(
                "A demo SKU is part of a paid order. No data was removed."
            )
        if any(
            order.items.exclude(variant_id__in=variant_ids).exists()
            for order in demo_orders
        ):
            raise CommandError(
                "A demo SKU is part of an order containing non-demo items. "
                "No data was removed."
            )

        if any(
            product.variants.exclude(sku__startswith=DEMO_SKU_PREFIX).exists()
            for product in demo_products
        ):
            raise CommandError(
                "Demo products contain non-demo variants. No data was removed."
            )

        item_count = CartItem.objects.filter(variant_id__in=variant_ids).delete()[0]
        movement_count = StockMovement.objects.filter(
            variant_id__in=variant_ids
        ).delete()[0]
        StockReservation.objects.filter(order_item__order_id__in=demo_order_ids).delete()
        order_count = demo_orders.count()
        demo_orders.delete()
        variant_count = variants.count()
        variants.delete()
        product_count = demo_products.count()
        demo_products.delete()
        empty_categories = Category.objects.filter(
            slug__in=DEMO_CATEGORY_SLUGS,
            products__isnull=True,
        )
        category_count = empty_categories.count()
        empty_categories.delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Removed demo data: "
                f"{category_count} categories, {product_count} products, "
                f"{variant_count} variants, {item_count} cart lines, "
                f"{order_count} orders, {movement_count} stock movements."
            )
        )
