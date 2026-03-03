from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Futsal, FutsalImage
from .serializers import FutsalSerializer, FutsalImageUploadSerializer
from rest_framework.permissions import IsAuthenticated

class FutsalViewSet(viewsets.ModelViewSet):
    queryset = Futsal.objects.all()
    serializer_class = FutsalSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

class FutsalImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FutsalImageUploadSerializer

    def post(self, request, futsal_uuid):
        futsal = Futsal.objects.get(uuid=futsal_uuid)

        if futsal.user != request.user:
            return Response(
                {"detail": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        images = serializer.validated_data["images"]

        for image in images:
            FutsalImage.objects.create(
                futsal=futsal,
                image=image
            )

        return Response(
            {"message": "Images uploaded successfully"},
            status=status.HTTP_201_CREATED
        )
