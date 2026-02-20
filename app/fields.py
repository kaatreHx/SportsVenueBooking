from rest_framework import serializers

class SimpleModelField(serializers.CharField):
    def __init__(self, model, serializer, lookup_field="id", **kwargs):
        self.model = model
        self.serializer = serializer
        self.lookup_field = lookup_field
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        # validate input is string
        data = super().to_internal_value(data)

        try:
            return self.model.objects.get(**{self.lookup_field: data})
        except self.model.DoesNotExist:
            raise serializers.ValidationError(
                f"{self.model.__name__} not found."
            )

    def to_representation(self, value):
        return self.serializer(value, context=self.parent.context).data