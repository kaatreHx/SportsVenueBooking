from rest_framework import serializers
from .models import User
from .sms_service import send_sms
from .otp_helper import generate_and_store_otp

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'password', 'full_name', 'address', 'city', 'is_active', 'is_staff', 'is_superuser', 'created_at']
        read_only_fields = ['id', 'is_active', 'is_staff', 'is_superuser', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.is_active = False
        user.save()
        #Test number "+18777804236"
        otp = generate_and_store_otp(user.phone)
        send_sms(user.phone, f"Your OTP is {otp}")
        return user

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'full_name', 'address', 'city', 'is_active', 'is_staff', 'is_superuser', 'created_at']
        read_only_fields = ['id', 'created_at']

class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
