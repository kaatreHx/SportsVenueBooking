from rest_framework import serializers
from .models import Futsal, FutsalImage
from user.serializers import UserSerializer
from booking.serializers import TimeSlotSerializer
from django.utils import timezone


class FutsalImageUploadSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False
    )


class FutsalImageBulkDeleteSerializer(serializers.Serializer):
    image_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )


class FutsalImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = FutsalImage
        fields = ("uuid", "image")

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class FutsalListSerializer(serializers.ModelSerializer):
    """Lightweight serializer used for list endpoints — no time_slots, annotated counts."""
    images = FutsalImageSerializer(many=True, read_only=True)

    # These are populated via queryset annotations in FutsalViewSet.get_queryset()
    available_slots_count = serializers.IntegerField(read_only=True)
    total_slots_count = serializers.IntegerField(read_only=True)
    is_open_now = serializers.SerializerMethodField()

    class Meta:
        model = Futsal
        fields = [
            "uuid", "name",
            "address", "city",
            "contact_number_primary", "contact_number_secondary",
            "price_per_hour",
            "is_active", "approval_status",
            "venue_type",
            "wifi", "washroom", "parking",
            "opening_time", "closing_time",
            "images",
            "available_slots_count", "total_slots_count", "is_open_now",
            "updated_at",
        ]

    def get_is_open_now(self, obj):
        now = timezone.localtime(timezone.now()).time()
        return obj.opening_time <= now <= obj.closing_time


class FutsalSerializer(serializers.ModelSerializer):
    """Full serializer used for create/update/detail — includes time_slots."""
    user = UserSerializer(read_only=True)
    images = FutsalImageSerializer(many=True, read_only=True)
    time_slots = TimeSlotSerializer(many=True, read_only=True)

    available_slots_count = serializers.SerializerMethodField()
    total_slots_count = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()

    class Meta:
        model = Futsal
        fields = [
            "uuid", "name", "user",
            "latitude", "longitude",
            "address", "city",
            "contact_number_primary", "contact_number_secondary",
            "price_per_hour",
            "is_active", "approval_status",
            "venue_type",
            "wifi", "washroom", "parking",
            "opening_time", "closing_time",
            "images", "time_slots",
            "available_slots_count", "total_slots_count", "is_open_now",
            "created_at", "updated_at",
        ]
        read_only_fields = ("uuid", "user", "created_at", "updated_at")

    def get_available_slots_count(self, obj):
        # Use annotation if available (avoids extra query), else fallback
        if hasattr(obj, 'available_slots'):
            return obj.available_slots
        return obj.time_slots.filter(is_active=True).count()

    def get_total_slots_count(self, obj):
        if hasattr(obj, 'total_slots'):
            return obj.total_slots
        return obj.time_slots.count()

    def get_is_open_now(self, obj):
        now = timezone.localtime(timezone.now()).time()
        return obj.opening_time <= now <= obj.closing_time

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if request and request.method == "POST":
            if not user or not user.is_vendor:
                raise serializers.ValidationError(
                    "Only venue owners can create a futsal."
                )
            if Futsal.objects.filter(user=user).exists():
                raise serializers.ValidationError(
                    "You have already created a futsal."
                )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        return Futsal.objects.create(user=request.user, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
