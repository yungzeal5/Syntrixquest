from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import CustomerAddress, CustomerProfile


class CustomerRegistrationSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate_username(self, value):
        user_model = get_user_model()
        username = user_model.normalize_username(value)
        if user_model._default_manager.filter(username=username).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return username

    def validate_email(self, value):
        if value is None:
            return None

        email = value.strip().lower()
        if not email:
            return ""

        user_model = get_user_model()
        if (
            CustomerProfile.objects.filter(email__iexact=email).exists()
            or user_model._default_manager.filter(email__iexact=email).exists()
        ):
            raise serializers.ValidationError("A customer with this email already exists.")
        return email

    def validate(self, attrs):
        user_model = get_user_model()
        user = user_model(
            username=attrs["username"],
            email=attrs.get("email") or "",
        )
        try:
            password_validation.validate_password(attrs["password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        user_model = get_user_model()
        email = validated_data.get("email") or ""
        username = validated_data["username"]

        try:
            with transaction.atomic():
                user = user_model._default_manager.create_user(
                    username=username,
                    email=email,
                    password=validated_data["password"],
                )
                profile, _ = CustomerProfile.objects.get_or_create(user=user)
                profile.email = email or None
                profile.save(update_fields=["email"])
        except IntegrityError:
            if email and CustomerProfile.objects.filter(email__iexact=email).exists():
                raise serializers.ValidationError(
                    {"email": "A customer with this email already exists."}
                ) from None
            if user_model._default_manager.filter(username=username).exists():
                raise serializers.ValidationError(
                    {"username": "A user with this username already exists."}
                ) from None
            raise

        return user


class SessionLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )


class SessionUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True, allow_blank=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, user):
        if user.is_superuser:
            return []
        return sorted(user.get_all_permissions())


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "The passwords do not match."}
            )
        return attrs


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = (
            "id",
            "label",
            "recipient_name",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "city",
            "region",
            "postal_code",
            "country_code",
            "delivery_instructions",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_country_code(self, value):
        return value.upper()
