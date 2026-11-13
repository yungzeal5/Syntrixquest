from rest_framework.permissions import SAFE_METHODS, BasePermission


class StaffModelPermissions(BasePermission):
    permission_actions = {
        "GET": "view",
        "HEAD": "view",
        "OPTIONS": "view",
        "POST": "add",
        "PUT": "change",
        "PATCH": "change",
        "DELETE": "delete",
    }

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not user.is_staff:
            return False

        action = self.permission_actions.get(request.method)
        if action is None:
            return False

        model = view.get_queryset().model
        permission = f"{model._meta.app_label}.{action}_{model._meta.model_name}"
        return user.has_perm(permission)


class PublicReadStaffModelPermissions(StaffModelPermissions):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().has_permission(request, view)
