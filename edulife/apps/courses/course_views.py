from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.users.permissions.core_permissions import IsTeacher
from apps.courses.serializers.course_serializers import CourseSerializer
from apps.courses.models import Course

class CreateCourseAPIView (CreateAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = CourseSerializer
