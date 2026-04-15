from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration with email and password confirmation."""

    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    class Meta:
        model = User
        fields = ["email", "password", "password2"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with email and password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled.")
        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data (returned on login and profile GET)."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "street_address",
            "city",
            "state",
            "zip_code",
            "phone_number",
            "date_of_birth",
            "insurance_provider",
            "plan_type",
            "language_pref",
            "email_verified",
        ]
        read_only_fields = ["id", "email", "email_verified"]


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating a user's profile fields."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "street_address",
            "city",
            "state",
            "zip_code",
            "phone_number",
            "date_of_birth",
            "insurance_provider",
            "plan_type",
            "language_pref",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing a user's password (requires current password)."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset email."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset with uid/token."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
