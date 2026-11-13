from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.catalog.models import ProductVariant

from .models import StockBalance


@receiver(post_save, sender=ProductVariant)
def create_stock_balance(sender, instance, created, **kwargs):
    if created:
        StockBalance.objects.create(variant=instance)
