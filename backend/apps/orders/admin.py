from django.contrib import admin

from .models import Order, OrderItem, StockReservation


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "variant",
        "product_name",
        "variant_label",
        "sku",
        "pack_quantity",
        "pack_unit",
        "unit_price",
        "quantity",
        "line_total",
    )
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "status",
        "contact_email",
        "items_subtotal",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("public_id", "contact_email", "items__sku")
    readonly_fields = (
        "public_id",
        "user",
        "guest_token_hash",
        "status",
        "contact_email",
        "recipient_name",
        "phone_number",
        "address_line_1",
        "address_line_2",
        "city",
        "region",
        "postal_code",
        "country_code",
        "delivery_instructions",
        "items_subtotal",
        "paid_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = (
        "order_item",
        "quantity",
        "released_at",
        "converted_at",
        "created_at",
    )
    list_filter = ("released_at", "converted_at")
    readonly_fields = (
        "order_item",
        "quantity",
        "released_at",
        "converted_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

