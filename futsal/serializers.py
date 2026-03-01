from rest_framework import serializers
from .models import Futsal
from user.serializers import UserSerializer

class FutsalSerializer(serializers.ModelSerializer):
    image_id = serializers.ListField(child=serializers.UUIDField(), required=False)
    user = UserSerializer(read_only=True)
    class Meta:
        model = Futsal
        fields = '__all__'
        read_only_fields = ('uuid', 'user', 'created_at')
    
    def create(self, validated_data):
        # image_ids = validated_data.pop('image_id', [])
        user = self.context['request'].user
        
        # Assign user before creation to avoid IntegrityError
        futsal = Futsal.objects.create(user=user, **validated_data)
        
        # for image_id in image_ids:
        #     content_type = ContentType.objects.get_for_model(Futsal)
        #     Attachment.objects.create(content_type=content_type, object_id=futsal.uuid, file=image_id)
        return futsal
    
    # def update(self, instance, validated_data):
        