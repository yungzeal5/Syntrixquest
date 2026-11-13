from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.viewsets import ModelViewSet

from apps.core.pagination import StandardPagination
from apps.core.permissions import StaffModelPermissions

from .models import CustomerFeedback
from .serializers import (
    CustomerFeedbackCreateSerializer,
    StaffCustomerFeedbackSerializer,
)


class CustomerFeedbackCreateView(generics.CreateAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    serializer_class = CustomerFeedbackCreateSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "feedback_submit"

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user if user.is_authenticated else None)


class StaffCustomerFeedbackViewSet(ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [StaffModelPermissions]
    serializer_class = StaffCustomerFeedbackSerializer
    pagination_class = StandardPagination
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return CustomerFeedback.objects.select_related("user").all()
