from rest_framework import viewsets
from .models import TimeSlot, Bookings, PaymentProof, CancelFine
from .serializers import TimeSlotSerializer, BookingsSerializer, PaymentProofSerializer
from .helper import calculate_cancellation_fine
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .enum import BookingStatus
from rest_framework.views import APIView
from datetime import datetime, timedelta
from django.db.models import Sum

class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

class BookingsViewSet(viewsets.ModelViewSet):
    queryset = Bookings.objects.all()
    serializer_class = BookingsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(detail=False, methods=['get'])
    def me(self, request):
        bookings = Bookings.objects.filter(user=request.user)
        serializer = BookingsSerializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def my_bookings(self, request):
        bookings = Bookings.objects.filter(user=request.user)
        serializer = BookingsSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.status = BookingStatus.CANCELLED
        booking.save()
        fine = calculate_cancellation_fine(booking)
        CancelFine.objects.create(booking=booking, fine=fine)
        #Email to user about cancellation
        return Response({'status': 'cancelled'})


class PaymentProofViewSet(viewsets.ModelViewSet):
    queryset = PaymentProof.objects.all()
    serializer_class = PaymentProofSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

class AvailableSlotsAPIView(APIView):

    def get(self, request, futsal_uuid):

        date = request.query_params.get("date")

        if not date:
            return Response(
                {"detail": "Date is required"},
                status=400
            )

        futsal = Futsal.objects.get(uuid=futsal_uuid)

        booked_slot_ids = Bookings.objects.filter(
            futsal=futsal,
            required_date=date,
            status__in=["PENDING", "CONFIRMED"]
        ).values_list("time_slot_id", flat=True)

        available_slots = TimeSlot.objects.filter(
            futsal=futsal,
            is_active=True
        ).exclude(
            id__in=booked_slot_ids
        )

        serializer = TimeSlotSerializer(available_slots, many=True)

        return Response(serializer.data)
        
class StaffDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Bookings.objects.all()

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # Pending requests
        book_requests = queryset.filter(status="PENDING").count()

        # Today's confirmed matches
        todays_matches = queryset.filter(
            required_date=today,
            status="CONFIRMED"
        ).count()

        # Today & Yesterday counts
        today_count = queryset.filter(
            required_date=today,
            status="CONFIRMED"
        ).count()

        yesterday_count = queryset.filter(
            required_date=yesterday,
            status="CONFIRMED"
        ).count()

        # Growth %
        if yesterday_count == 0:
            request_growth = 100 if today_count > 0 else 0
        else:
            request_growth = ((today_count - yesterday_count) / yesterday_count) * 100

        # Total revenue from all confirmed bookings
        revenue = queryset.filter(
            status="CONFIRMED"
        ).aggregate(total=Sum("total_price"))["total"] or 0

        return Response({
            "booking_requests": book_requests,
            "todays_matches": todays_matches,
            "request_growth_percent": round(request_growth, 2),
            "revenue": revenue
        })
