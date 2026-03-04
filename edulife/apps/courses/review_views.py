from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.courses.models import Review, Course
from apps.courses.serializers.course_serializers import ReviewSerializer
from apps.courses.permissions.course_permissions import IsEnrolled
from apps.users.models import CustomUser


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления отзывами о курсах.
    - list: Получить все отзывы по курсу (параметр: course_id) — любой студент
    - retrieve: Получить конкретный отзыв — любой студент
    - create: Создать отзыв (только студенты, должны быть записаны на курс)
    - update/partial_update: Обновить свой отзыв (заблокировано после публикации курса)
    - destroy: Удалить свой отзыв (заблокировано после публикации курса)
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

    def perform_destroy(self, instance):
        if instance.course.status == Course.CourseStatus.PUBLISHED:
            raise ValidationError({"detail": "Reviews cannot be deleted after course publication."})
        instance.delete()
