from rest_framework import serializers
from .models import User
from .otp_helper import generate_and_store_otp
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class CustomLoginSerializer(TokenObtainPairSerializer):
    """
    Accepts { "login": "<phone>", "password": "<pw>" }
    login can be phone number (with or without +977 prefix).
    Returns access, refresh, role, full_name, is_vendor.
    """
    login = serializers.CharField(write_only=True)

    def to_internal_value(self, data):
        # Make a mutable copy so we can inject 'phone'
        data = data.copy()
        login = data.get("login", "").strip()

        if not login:
            raise serializers.ValidationError({"login": "Phone number is required"})

        # Normalise: strip +977 or 977 prefix, keep digits only
        phone = re.sub(r'^\+?977', '', login).strip()
        # Try exact match first, then without country code
        user = None
        for candidate in [login, phone, f'+977{phone}', f'977{phone}']:
            try:
                user = User.objects.get(phone=candidate)
                break
            except User.DoesNotExist:
                continue

        if user is None:
            raise serializers.ValidationError({"login": "No account found with this phone number"})

        # Inject the stored phone so SimpleJWT can authenticate
        data["phone"] = user.phone
        return super().to_internal_value(data)

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = "vendor" if self.user.is_vendor else "player"
        data["full_name"] = self.user.full_name
        data["is_vendor"] = self.user.is_vendor
        data["uuid"] = str(self.user.uuid)
        return data


def _unique_username(base: str) -> str:
    """Generate a unique username from a base string."""
    base = re.sub(r'\s+', '', base).lower() or 'user'
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'uuid', 'phone', 'password', 'full_name',
            'address', 'is_active', 'is_vendor',
            'created_at', 'document', 'profile_picture',
        ]
        read_only_fields = ['uuid', 'is_active', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'document': {'required': False, 'allow_null': True},
            'profile_picture': {'required': False, 'allow_null': True},
            'address': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            user.is_active = True
            user.username = _unique_username(user.full_name)
            user.save()
            otp = generate_and_store_otp(user.phone)

        # In development, print OTP to console (SMS disabled)
        print(f"[DEV] OTP for {user.phone}: {otp}")

        # Attach otp to instance so the view can return it
        user._otp = otp
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'uuid', 'username', 'phone', 'full_name',
            'address', 'is_active', 'is_vendor', 'created_at',
        ]
        read_only_fields = ['uuid', 'created_at']


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6)
