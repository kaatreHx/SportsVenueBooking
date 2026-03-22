from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count

from .models import Futsal, FutsalImage
from .serializers import (
    FutsalSerializer,
    FutsalListSerializer,
    FutsalImageUploadSerializer,
    FutsalImageBulkDeleteSerializer,
)


class FutsalViewSet(viewsets.ModelViewSet):
    """
    Public GET  /futsal/futsals/          → all active venues (lightweight list)
    Public GET  /futsal/futsals/<uuid>/   → single venue detail (full)
    Auth  POST  /futsal/futsals/          → create venue (vendor only)
    Auth  PATCH /futsal/futsals/<uuid>/   → update venue (owner only)
    Auth  DELETE/futsal/futsals/<uuid>/   → delete venue (owner only)
    Auth  GET   /futsal/futsals/me/       → current vendor's venues
    """
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        # Use the lightweight serializer for list; full serializer for everything else
        if self.action == 'list':
            return FutsalListSerializer
        return FutsalSerializer

    def get_queryset(self):
        qs = Futsal.objects.filter(is_active=True)

        if self.action == 'list':
            # Annotate slot counts at DB level — avoids N+1 queries
            qs = qs.annotate(
                available_slots=Count(
                    'time_slots',
                    filter=Q(time_slots__is_active=True),
                ),
                total_slots=Count('time_slots'),
            ).prefetch_related('images').select_related('user')
        else:
            qs = qs.prefetch_related('images', 'time_slots').select_related('user')

        # Search by name, city, or address
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(city__icontains=search) |
                Q(address__icontains=search)
            )

        # Filter by city
        city = self.request.query_params.get('city', '').strip()
        if city:
            qs = qs.filter(city__icontains=city)

        # Filter by venue type (Indoor / Outdoor)
        venue_type = self.request.query_params.get('venue_type', '').strip()
        if venue_type:
            qs = qs.filter(venue_type__iexact=venue_type)

        # Filter: available now (has at least one active time slot + currently open)
        available_now = self.request.query_params.get('available_now', '').strip().lower()
        if available_now == 'true':
            now = timezone.localtime(timezone.now()).time()
            qs = qs.filter(
                opening_time__lte=now,
                closing_time__gte=now,
                time_slots__is_active=True,
            ).distinct()

        # Sort
        sort = self.request.query_params.get('sort', '').strip().lower()
        if sort == 'price_asc':
            qs = qs.order_by('price_per_hour')
        elif sort == 'price_desc':
            qs = qs.order_by('-price_per_hour')
        else:
            qs = qs.order_by('-updated_at')

        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit your own venue.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own venue.")
        instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Returns all venues belonging to the authenticated vendor."""
        if not request.user.is_vendor:
            return Response(
                {"detail": "Only venue owners can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )
        futsals = Futsal.objects.filter(user=request.user).annotate(
            available_slots=Count(
                'time_slots',
                filter=Q(time_slots__is_active=True),
            ),
            total_slots=Count('time_slots'),
        ).prefetch_related('images', 'time_slots')
        serializer = FutsalSerializer(futsals, many=True, context={'request': request})
        return Response(serializer.data)


class FutsalImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, futsal_uuid):
        futsal = get_object_or_404(Futsal, uuid=futsal_uuid)

        if futsal.user != request.user:
            return Response(
                {"detail": "Not allowed."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = FutsalImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        objs = [
            FutsalImage(futsal=futsal, image=image)
            for image in serializer.validated_data["images"]
        ]
        FutsalImage.objects.bulk_create(objs)

        futsal.save(update_fields=['updated_at'])

        return Response(
            {"message": "Images uploaded successfully."},
            status=status.HTTP_201_CREATED,
        )


class FutsalImageBulkDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, futsal_uuid):
        futsal = get_object_or_404(Futsal, uuid=futsal_uuid)

        if futsal.user != request.user:
            return Response(
                {"detail": "Not allowed."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = FutsalImageBulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        images_qs = FutsalImage.objects.filter(
            futsal=futsal,
            uuid__in=serializer.validated_data["image_uuids"],
        )

        for img in images_qs:
            if img.image:
                img.image.delete(save=False)

        deleted_count, _ = images_qs.delete()

        futsal.save(update_fields=['updated_at'])

        return Response(
            {"message": "Images deleted.", "deleted_count": deleted_count},
            status=status.HTTP_200_OK,
        )
