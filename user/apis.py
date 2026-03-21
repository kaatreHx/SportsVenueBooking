from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from .models import User
from .serializers import UserSerializer, UserRegisterSerializer, VerifyOTPSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework import generics
from rest_framework.views import APIView
from .otp_helper import verify_otp
from django.db.models import Count, Sum, F, Q, ExpressionWrapper, DurationField
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomLoginSerializer

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomLoginSerializer

class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

class VerifyOTP(APIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(phone=serializer.validated_data['phone'])
            if verify_otp(user.phone, serializer.validated_data['otp']):
                user.is_active = True
                user.save()
                return JsonResponse({'message': 'OTP verified successfully'}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'message': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserAPIView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'patch', 'delete']
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class WeeklyLeaderboardAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())

        duration_expr = ExpressionWrapper(
            F("bookings__time_slot__end_time") - F("bookings__time_slot__start_time"),
            output_field=DurationField()
        )

        players = (
            User.objects.filter(is_vendor=False)
            .annotate(
                matches_played_week=Count(
                    "bookings",
                    filter=Q(
                        bookings__status="COMPLETED",
                        bookings__required_date__gte=week_start,
                        bookings__required_date__lte=today,
                    ),
                ),
                hour_played_week=Sum(
                    duration_expr,
                    filter=Q(
                        bookings__status="COMPLETED",
                        bookings__required_date__gte=week_start,
                        bookings__required_date__lte=today,
                    ),
                ),
            )
            .filter(matches_played_week__gt=0)
            .order_by("-hour_played_week", "-matches_played_week")[:10]
        )

        leaderboard = []
        for rank, player in enumerate(players, start=1):
            hours = (
                player.hour_played_week.total_seconds() / 3600
                if player.hour_played_week
                else 0
            )

            leaderboard.append({
                "rank": rank,
                "full_name": player.full_name,
                "profile_picture": player.profile_picture.url if player.profile_picture else None,
                "hours_played_week": round(hours, 2),
                "matches_played_week": player.matches_played_week,
                "score": round(hours * 10 + player.matches_played_week, 2),
            })

        return Response(leaderboard)