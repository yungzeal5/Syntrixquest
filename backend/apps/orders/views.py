from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import APIException, NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.services import (
    GUEST_CART_COOKIE_NAME,
    attach_guest_cookie,
    hash_guest_token,
    resolve_cart,
)
from apps.core.pagination import StandardPagination
from apps.core.permissions import StaffModelPermissions

from .models import Order
from .serializers import (
    CheckoutSerializer,
    OrderSerializer,
    StaffOrderQueueSerializer,
)
from .services import (
    EmptyCartError,
    OrderStateError,
    OutOfStockError,
    cancel_order,
    create_order_from_cart,
)


class OrderConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The order cannot be completed in its current state."
    default_code = "order_conflict"


@method_decorator(csrf_protect, name="dispatch")
class CheckoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_context = resolve_cart(request)
        if cart_context.cart is None:
            return Response(
                {"detail": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token_hash = (
            hash_guest_token(cart_context.guest_token)
            if not request.user.is_authenticated and cart_context.guest_token
            else None
        )
        try:
            order = create_order_from_cart(
                cart=cart_context.cart,
                contact=serializer.validated_data,
                user=request.user,
                guest_token_hash=token_hash,
            )
        except EmptyCartError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except OutOfStockError as exc:
            raise OrderConflict(str(exc)) from exc

        response = Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return attach_guest_cookie(response, cart_context)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items")
            .order_by("-created_at", "-id")
        )


class StaffOrderQueueView(generics.ListAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [StaffModelPermissions]
    serializer_class = StaffOrderQueueSerializer
    pagination_class = StandardPagination
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return Order.objects.prefetch_related("items").order_by(
            "-created_at",
            "-id",
        )


class OrderDetailView(APIView):
    permission_classes = [AllowAny]

    def get_order(self, request, public_id):
        orders = Order.objects.prefetch_related("items")
        if request.user.is_authenticated:
            order = orders.filter(user=request.user, public_id=public_id).first()
            if order:
                return order
            token = request.COOKIES.get(GUEST_CART_COOKIE_NAME)
            if not token or len(token) > 128:
                return None
            guest_order = orders.filter(
                guest_token_hash=hash_guest_token(token),
                user__isnull=True,
                public_id=public_id,
            ).first()
            return guest_order

        token = request.COOKIES.get(GUEST_CART_COOKIE_NAME)
        if not token or len(token) > 128:
            return None
        return orders.filter(
            guest_token_hash=hash_guest_token(token),
            public_id=public_id,
        ).first()

    def get(self, request, public_id):
        order = self.get_order(request, public_id)
        if order is None:
            raise NotFound("Order not found.")
        return Response(OrderSerializer(order).data)


@method_decorator(csrf_protect, name="dispatch")
class OrderCancelView(OrderDetailView):
    def post(self, request, public_id):
        order = self.get_order(request, public_id)
        if order is None:
            raise NotFound("Order not found.")
        try:
            order = cancel_order(order.public_id)
        except OrderStateError as exc:
            raise OrderConflict(str(exc)) from exc
        return Response(OrderSerializer(order).data)
