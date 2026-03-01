from rest_framework import viewsets
from .models import Futsal
from .serializers import FutsalSerializer
from rest_framework.permissions import IsAuthenticated

class FutsalViewSet(viewsets.ModelViewSet):
    queryset = Futsal.objects.all()
    serializer_class = FutsalSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

