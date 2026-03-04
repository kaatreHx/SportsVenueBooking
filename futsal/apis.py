from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Futsal, FutsalImage
from .serializers import FutsalSerializer, FutsalImageUploadSerializer, FutsalImageBulkDeleteSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import get_object_or_404

class FutsalViewSet(viewsets.ModelViewSet):
    queryset = Futsal.objects.all()
    serializer_class = FutsalSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        if not request.user.is_vendor:
            return Response(
                {"detail": "You are not authorized to view this resource."},
                status=status.HTTP_403_FORBIDDEN
            )

        futsals = Futsal.objects.filter(user=request.user)

        serializer = FutsalSerializer(futsals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class FutsalImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FutsalImageUploadSerializer

    def post(self, request, futsal_uuid):
        futsal = get_object_or_404(Futsal, uuid=futsal_uuid)

        if futsal.user != request.user:
            return Response(
                {"detail": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        images = serializer.validated_data["images"]

        objs = [
            FutsalImage(futsal=futsal, image=image)
            for image in images
        ]
        FutsalImage.objects.bulk_create(objs)

        return Response(
            {"message": "Images uploaded successfully"},
            status=status.HTTP_201_CREATED
        )

class FutsalImageBulkDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FutsalImageBulkDeleteSerializer

    def post(self, request, futsal_uuid):
        futsal = get_object_or_404(Futsal, uuid=futsal_uuid)

        # ownership check
        if futsal.user != request.user:
            return Response(
                {"detail": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_uuids = serializer.validated_data["image_uuids"]

        images_qs = FutsalImage.objects.filter(
            futsal=futsal,
            uuid__in=image_uuids
        )

        # delete files from storage first
        for img in images_qs:
            if img.image:
                img.image.delete(save=False)

        deleted_count, _ = images_qs.delete()

        return Response(
            {
                "message": "Images deleted successfully",
                "deleted_count": deleted_count
            },
            status=status.HTTP_200_OK
        )

