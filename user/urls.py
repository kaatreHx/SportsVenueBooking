from django.urls import path, include
from . import apis
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', apis.UserAPIView, basename='user')

urlpatterns = [
    path('register/', apis.RegisterAPIView.as_view(), name='register'),
    path('verify-otp/', apis.VerifyOTP.as_view(), name='verify_otp'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh-token/', jwt_views.TokenRefreshView.as_view(), name='refresh'),
    path('accounts/', include(router.urls))
]