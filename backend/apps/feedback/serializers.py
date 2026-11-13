from rest_framework import serializers

from .models import CustomerFeedback


class CustomerFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFeedback
        fields = ("name", "email", "category", "message")
        extra_kwargs = {
            "name": {"required": False},
            "email": {"required": False},
            "category": {"required": False},
        }

    def validate_name(self, value):
        return value.strip()

    def validate_message(self, value):
        message = value.strip()
        if not message:
            raise serializers.ValidationError("Feedback cannot be blank.")
        return message


class StaffCustomerFeedbackSerializer(serializers.ModelSerializer):
    submitted_by = serializers.CharField(
        source="user.username",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = CustomerFeedback
        fields = (
            "id",
            "name",
            "email",
            "category",
            "message",
            "status",
            "staff_notes",
            "submitted_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "name",
            "email",
            "category",
            "message",
            "submitted_by",
            "created_at",
            "updated_at",
        )
