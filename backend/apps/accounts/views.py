from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.middleware.csrf import get_token
from django.utils.encoding import force_str
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .serializers import (
    CustomerAddressSerializer,
    CustomerRegistrationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    SessionLoginSerializer,
    SessionUserSerializer,
)


class CustomerRegistrationView(generics.CreateAPIView):
    serializer_class = CustomerRegistrationSerializer
    permission_classes = [AllowAny]


class CSRFCookieView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request._request)})


@method_decorator(csrf_protect, name="dispatch")
class SessionLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SessionLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request._request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request._request, user)
        return Response(SessionUserSerializer(user).data)


@method_decorator(csrf_protect, name="dispatch")
class SessionLogoutView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionUserView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(SessionUserSerializer(request.user).data)


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        form = PasswordResetForm(data=serializer.validated_data)
        if not form.is_valid():
            errors = {
                field: [str(error) for error in field_errors]
                for field, field_errors in form.errors.items()
            }
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        form.save(
            request=request._request,
            from_email=settings.DEFAULT_FROM_EMAIL,
            subject_template_name="accounts/password_reset_subject.txt",
            email_template_name="accounts/password_reset_email.txt",
            extra_email_context={
                "frontend_url": settings.PASSWORD_RESET_FRONTEND_URL,
            },
        )
        return Response(
            {
                "detail": (
                    "If an account with that email exists, reset instructions "
                    "will be sent."
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_confirm"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_user(serializer.validated_data["uid"])
        if user is None or not default_token_generator.check_token(
            user, serializer.validated_data["token"]
        ):
            return Response(
                {"detail": "This password-reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        form = SetPasswordForm(
            user,
            data={
                "new_password1": serializer.validated_data["new_password"],
                "new_password2": serializer.validated_data["new_password_confirm"],
            },
        )
        if not form.is_valid():
            errors = form.errors.get("new_password2") or form.errors.get(
                "new_password1"
            )
            return Response(
                {"new_password": list(errors)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        form.save()
        return Response({"detail": "Your password has been reset."})

    @staticmethod
    def get_user(uidb64):
        user_model = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return user_model._default_manager.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UnicodeError,
            user_model.DoesNotExist,
        ):
            return None


class CustomerAddressListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerAddressSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.customer_addresses.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CustomerAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerAddressSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.customer_addresses.all()
