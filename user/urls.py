from django.urls import path, include
from . import apis
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.routers import DefaultRouter
from django.conf import settings

router = DefaultRouter()
router.register(r'users', apis.UserAPIView, basename='user')

auth_patterns = [
    path('register/', apis.RegisterAPIView.as_view(), name='register'),
    path('verify-otp/', apis.VerifyOTP.as_view(), name='verify_otp'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh-token/', jwt_views.TokenRefreshView.as_view(), name='refresh'),
]

# Dev-only: get raw OTP from cache (remove in production)
if settings.DEBUG:
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import AllowAny
    from rest_framework.response import Response
    from django.core.cache import cache
    from .otp_helper import hash_otp

    @api_view(['GET'])
    @permission_classes([AllowAny])
    def dev_get_otp(request):
        """DEV ONLY — returns cached OTP hash for a phone number.
        Check Django console for the raw OTP printed as [OTP] <phone> → <otp>"""
        phone = request.query_params.get('phone', '')
        cached = cache.get(f"otp:{phone}")
        return Response({'phone': phone, 'otp_cached': bool(cached)})

    auth_patterns += [path('dev-otp/', dev_get_otp, name='dev_otp')]

urlpatterns = [
    path('auth/', include(auth_patterns)),
    path('users/', include(router.urls))
]