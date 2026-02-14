from apps.users.models import CustomUser
from apps.courses.models import Course,Module,Task
from apps.courses.permissions.course_permissions import IsTeacher
from django.shortcuts import get_object_or_404
from apps.courses.serializers.course_serializers import (
    CreateCourseSerializer,
    ModuleSerializer,
    TaskSerializer,
)
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly


class CreateCourseAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated,IsTeacher]
    serializer_class = CreateCourseSerializer

    def create(self,request,*args):
        teacher = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(teacher=teacher)
        return Response(serializer.data, status=status.HTTP_201_CREATED )


class CreateModuleAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated,IsTeacher]
    serializer_class = ModuleSerializer

    def create(self, request, *args, **kwargs):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, id=course_id, teacher=self.request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(course=course)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class CreateTaskAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated,IsTeacher]
    serializer_class = TaskSerializer

    def create(self,request,*args,**kwargs):
        module_id = kwargs['module_id']
        module = get_object_or_404(Module,id=module_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(module=module)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    