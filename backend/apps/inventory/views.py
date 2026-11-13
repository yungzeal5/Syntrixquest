from rest_framework import mixins, viewsets
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.pagination import StandardPagination
from apps.core.permissions import StaffModelPermissions

from .models import StockBalance, StockMovement
from .serializers import StockBalanceSerializer, StockMovementSerializer


class StockBalanceViewSet(ReadOnlyModelViewSet):
    queryset = StockBalance.objects.select_related("variant", "variant__product")
    serializer_class = StockBalanceSerializer
    permission_classes = [StaffModelPermissions]
    pagination_class = StandardPagination


class StockMovementViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = StockMovement.objects.select_related("variant", "created_by")
    serializer_class = StockMovementSerializer
    permission_classes = [StaffModelPermissions]
    pagination_class = StandardPagination
