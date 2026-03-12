from rest_framework import viewsets
from .models import Review
from .serializer import ReviewSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(detail=False, methods=['get'])
    def futsal_reviews(self, request, futsal_id):
        reviews = Review.objects.filter(futsal=futsal_id)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)