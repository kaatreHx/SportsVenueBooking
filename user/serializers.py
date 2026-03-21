from rest_framework import serializers
from .models import User
from .sms_service import send_sms
from .otp_helper import generate_and_store_otp
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomLoginSerializer(TokenObtainPairSerializer):
    login = serializers.CharField(write_only=True)

    def to_internal_value(self, data):
        login = data.get("login")

        if not login:
            raise serializers.ValidationError({"login": "Email or phone is required"})

        try:
            if "@" in login:
                user = User.objects.get(email=login)
            else:
                user = User.objects.get(phone=login)
                print("User Phone", user.phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"login": "User not found"})

        # 🔥 Inject required USERNAME_FIELD BEFORE validation
        data["phone"] = user.phone

        return super().to_internal_value(data)

    def validate(self, attrs):
        # default JWT validation (returns access + refresh only)
        return super().validate(attrs)

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uuid', 'email', 'phone', 'password', 'full_name', 'address', 'is_active', 'is_vendor', 'is_superuser', 'created_at', 'document', 'profile_picture']
        read_only_fields = ['uuid', 'is_active', 'is_superuser', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, attrs):
        if attrs.get('is_vendor') and not attrs.get('document'):
            raise serializers.ValidationError("Document is required for vendors")
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            user.is_active = True
            user.save()
            otp = generate_and_store_otp(user.phone)
            user.username = user.full_name.replace(" ", "").lower()
            user.save()
            
        
        # SMS outside transaction - user still created if this fails
        # try:
        #     send_sms(user.phone, f"Your OTP is {otp}")
        # except Exception as e:
        #     # Log the error but don't fail registration
        #     print(f"SMS failed: {e}")
        
        return user

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uuid', 'username', 'email', 'phone', 'full_name', 'address', 'is_active', 'is_vendor', 'is_superuser', 'created_at']
        read_only_fields = ['uuid', 'created_at']

class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)