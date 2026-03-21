from rest_framework import serializers
from .models import User
from .sms_service import send_sms
from .otp_helper import generate_and_store_otp
from django.db import transaction
import re


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'uuid', 'username', 'email', 'phone', 'password',
            'full_name', 'address', 'is_active', 'is_vendor',
            'is_superuser', 'created_at', 'document', 'profile_picture',
        ]
        read_only_fields = ['uuid', 'is_active', 'is_superuser', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    def validate_phone(self, value):
        value = value.strip()
        if not re.match(r'^\+?[0-9]{7,15}$', value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate(self, attrs):
        if attrs.get('is_vendor') and not attrs.get('document'):
            raise serializers.ValidationError("Document is required for vendors.")
        return attrs

    def create(self, validated_data):
        # Auto-generate username from full_name + last 4 digits of phone
        if not validated_data.get('username'):
            phone = validated_data['phone']
            raw_name = (validated_data.get('full_name') or '').lower().replace(' ', '_')
            base = re.sub(r'[^a-z0-9_]', '', raw_name)
            suffix = re.sub(r'[^0-9]', '', phone)[-4:]
            candidate = f"{base}_{suffix}" if base else f"user_{suffix}"
            username = candidate
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{candidate}_{counter}"
                counter += 1
            validated_data['username'] = username

        # Remove blank email so it doesn't fail unique constraint
        if not validated_data.get('email'):
            validated_data.pop('email', None)

        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            user.is_active = False  # stays inactive until OTP verified
            user.save()
            otp = generate_and_store_otp(user.phone)

        # Log OTP to console for development (remove in production)
        print(f"[OTP] {user.phone} → {otp}")

        # Fire-and-forget SMS in background thread — never blocks the response
        send_sms(user.phone, f"Your FutsalApp OTP is {otp}. Valid for 60 seconds.")

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'uuid', 'username', 'email', 'phone', 'full_name',
            'address', 'is_active', 'is_vendor',
            'is_superuser', 'created_at',
        ]
        read_only_fields = ['uuid', 'created_at']


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
