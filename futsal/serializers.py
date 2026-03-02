from rest_framework import serializers
from .models import Futsal
from user.serializers import UserSerializer

class FutsalSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Futsal
        fields = "__all__"
        read_only_fields = ("uuid", "user", "created_at")

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if request and request.method == "POST":
            if not user or not user.is_vendor:
                raise serializers.ValidationError(
                    "You are not authorized to create a futsal."
                )

            if Futsal.objects.filter(user=user).exists():
                raise serializers.ValidationError(
                    "You have already created a futsal."
                )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        return Futsal.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        