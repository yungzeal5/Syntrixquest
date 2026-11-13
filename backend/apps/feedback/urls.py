from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomerFeedbackCreateView, StaffCustomerFeedbackViewSet

router = DefaultRouter()
router.register(
    "manage",
    StaffCustomerFeedbackViewSet,
    basename="feedback-management",
)

urlpatterns = [
    path("", CustomerFeedbackCreateView.as_view(), name="feedback-submit"),
    path("", include(router.urls)),
]
