from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from .models import User
from .serializers import UserSerializer, UserRegisterSerializer, VerifyOTPSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework import generics
from rest_framework.views import APIView
from .otp_helper import verify_otp
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.core.cache import cache


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_data = UserSerializer(user).data
            # In DEBUG mode, include OTP in response so dev can test without SMS
            if settings.DEBUG:
                cached = cache.get(f"otp:{user.phone}")
                response_data['_dev_otp_hash'] = cached  # hash only, not raw OTP
                # Raw OTP is printed to Django console: look for [OTP] in logs
            return JsonResponse(response_data, status=status.HTTP_201_CREATED)

        # Flatten field-level errors into a single readable message
        errors = serializer.errors
        messages = []
        for field, errs in errors.items():
            for e in errs:
                messages.append(str(e) if field == 'non_field_errors' else f"{field}: {e}")
        return JsonResponse(
            {'detail': ' | '.join(messages)},
            status=status.HTTP_400_BAD_REQUEST,
        )


class VerifyOTP(APIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return JsonResponse({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not verify_otp(phone, otp):
            return JsonResponse({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()

        # Issue JWT tokens
        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            'message': 'OTP verified successfully.',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)

class UserAPIView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'patch', 'delete']
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get or update current user profile"""
        user = request.user
        
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return JsonResponse(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data, status=status.HTTP_200_OK)
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    
