from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis import FutsalViewSet, FutsalImageUploadView, FutsalImageBulkDeleteView

router = DefaultRouter()
router.register(r'', FutsalViewSet, basename='futsal')

urlpatterns = [
    path('', include(router.urls)),
    path('<uuid:futsal_uuid>/images/', FutsalImageUploadView.as_view(), name='futsal-image-upload'),
    path('<uuid:futsal_uuid>/images/bulk-delete/', FutsalImageBulkDeleteView.as_view(), name='futsal-image-bulk-delete'),
]