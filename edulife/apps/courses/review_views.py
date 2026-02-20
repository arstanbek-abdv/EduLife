from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from apps.courses.models import Review
from apps.courses.serializers.course_serializers import ReviewSerializer
from apps.courses.permissions.course_permissions import IsEnrolled
from apps.users.models import CustomUser


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing course reviews.
    - list: Get all reviews for a specific course (query param: course_id)
    - retrieve: Get a specific review
    - create: Create a new review (students only, must be enrolled)
    - update/partial_update: Update own review (must be enrolled)
    - destroy: Delete own review (must be enrolled)
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsEnrolled]

    def get_queryset(self):
        queryset = Review.objects.select_related('student', 'course').all()
        
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset

    def perform_create(self, serializer):
        if self.request.user.role != CustomUser.Role.STUDENT:
            raise PermissionDenied("Only students can create reviews.")
        serializer.save(student=self.request.user)
