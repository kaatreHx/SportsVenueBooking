from rest_framework import routers
from .apis import ReviewViewSet

router = routers.DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = router.urls