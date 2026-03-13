from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis import TimeSlotViewSet, BookingsViewSet, PaymentProofViewSet, AvailableSlotsAPIView, StaffDashboardAPIView

router = DefaultRouter()
router.register(r'time-slots', TimeSlotViewSet, basename='time-slot')
router.register(r'bookings', BookingsViewSet, basename='booking')
router.register(r'payment-proofs', PaymentProofViewSet, basename='payment-proof')

urlpatterns = [
    path('', include(router.urls)),
    path('available-slots/<str:futsal_uuid>/<str:date>', AvailableSlotsAPIView.as_view(), name='available-slots'),
    path('staff-dashboard/', StaffDashboardAPIView.as_view(), name='staff-dashboard'),
]