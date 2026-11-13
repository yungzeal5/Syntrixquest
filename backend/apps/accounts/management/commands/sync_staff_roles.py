from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError

ROLE_GROUPS = (
    "Store Manager",
    "Order Manager",
    "Marketing Manager",
    "Customer Support",
)


class Command(BaseCommand):
    help = "Create staff role groups and grant permissions for implemented modules."

    def handle(self, *args, **options):
        groups = {
            name: Group.objects.get_or_create(name=name)[0] for name in ROLE_GROUPS
        }

        store_manager_permissions = []
        permission_sets = (
            ("catalog", "category", ("view", "add", "change", "delete")),
            ("catalog", "product", ("view", "add", "change", "delete")),
            ("catalog", "productvariant", ("view", "add", "change", "delete")),
            ("inventory", "stockbalance", ("view",)),
            ("inventory", "stockmovement", ("view", "add")),
        )
        for app_label, model, actions in permission_sets:
            for action in actions:
                codename = f"{action}_{model}"
                try:
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        content_type__model=model,
                        codename=codename,
                    )
                except Permission.DoesNotExist as exc:
                    raise CommandError(
                        f"Missing permission {codename}; run migrations first."
                    ) from exc
                store_manager_permissions.append(permission)

        groups["Store Manager"].permissions.add(*store_manager_permissions)
        customer_support_permissions = []
        permission_sets = (
            ("reviews", "productreview", ("view", "change")),
            ("feedback", "customerfeedback", ("view", "change")),
        )
        for app_label, model, actions in permission_sets:
            for action in actions:
                codename = f"{action}_{model}"
                try:
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        content_type__model=model,
                        codename=codename,
                    )
                except Permission.DoesNotExist as exc:
                    raise CommandError(
                        f"Missing permission {codename}; run migrations first."
                    ) from exc
                customer_support_permissions.append(permission)

        groups["Customer Support"].permissions.add(*customer_support_permissions)
        try:
            order_view_permission = Permission.objects.get(
                content_type__app_label="orders",
                content_type__model="order",
                codename="view_order",
            )
        except Permission.DoesNotExist as exc:
            raise CommandError(
                "Missing permission view_order; run migrations first."
            ) from exc
        groups["Order Manager"].permissions.add(order_view_permission)
        self.stdout.write(
            self.style.SUCCESS(
                "Staff role groups are ready. Store Manager has catalogue and "
                "inventory access. Customer Support can moderate product "
                "reviews and manage feedback. Order Manager can view orders."
            )
        )
