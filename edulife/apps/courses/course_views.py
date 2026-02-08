from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.users.permissions.core_permissions import IsTeacher

class CreateCourseAPIView (ModelViewSet):
    permission_classes = [IsAuthenticated, IsTeacher]
    