from rest_framework import viewsets
from .models import TimeSlot, Bookings, PaymentProof, CancelFine
from .serializers import TimeSlotSerializer, BookingsSerializer, PaymentProofSerializer
from .helper import calculate_cancellation_fine
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .enum import BookingStatus

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
