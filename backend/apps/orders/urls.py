from django.urls import path

from .views import (
    CheckoutView,
    OrderCancelView,
    OrderDetailView,
    OrderListView,
    StaffOrderQueueView,
)

urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/manage/", StaffOrderQueueView.as_view(), name="staff-order-queue"),
    path("orders/<uuid:public_id>/", OrderDetailView.as_view(), name="order-detail"),
    path(
        "orders/<uuid:public_id>/cancel/",
        OrderCancelView.as_view(),
        name="order-cancel",
    ),
]
