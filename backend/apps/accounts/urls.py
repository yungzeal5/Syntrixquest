from django.urls import path

from .views import (
    CSRFCookieView,
    CustomerAddressDetailView,
    CustomerAddressListCreateView,
    CustomerRegistrationView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    SessionLoginView,
    SessionLogoutView,
    SessionUserView,
)

urlpatterns = [
    path("csrf/", CSRFCookieView.as_view(), name="csrf-token"),
    path("login/", SessionLoginView.as_view(), name="session-login"),
    path("logout/", SessionLogoutView.as_view(), name="session-logout"),
    path("me/", SessionUserView.as_view(), name="session-user"),
    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("register/", CustomerRegistrationView.as_view(), name="customer-registration"),
    path(
        "addresses/",
        CustomerAddressListCreateView.as_view(),
        name="customer-address-list",
    ),
    path(
        "addresses/<int:pk>/",
        CustomerAddressDetailView.as_view(),
        name="customer-address-detail",
    ),
]
