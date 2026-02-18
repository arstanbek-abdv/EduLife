from apps.users.models import CustomUser
from apps.courses.models import Course,Module,Task
from apps.courses.permissions.course_permissions import IsTeacher
from django.shortcuts import get_object_or_404
from apps.courses.serializers.course_serializers import (
    CreateCourseSerializer,
    ModuleSerializer,
    TaskSerializer
)
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError

from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_502_BAD_GATEWAY,
)
from apps.courses.course_views import (ensure_bucket, 
    get_minio_client, 
    remove_object_if_exists, 
    normalize_clickable_url,
    )
from django.conf import settings 
from datetime import timedelta
from django.utils import timezone
import uuid 
import os 

from minio import Minio
from minio.error import S3Error

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
    
       
class CourseCoverUpload(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def course_teacher(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, teacher=request.user)
        self.check_object_permissions(request, course)
        return course

    def put(self, request, course_id, *args, **kwargs):
        course = self.course_teacher(request, course_id)
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'file': 'This field is required.'}, status=HTTP_400_BAD_REQUEST)
        ext = os.path.splitext(uploaded.name)[1]
        file_key = f'course_covers/{course.id}/{uuid.uuid4().hex}{ext}'

        client = get_minio_client()
        try:
            ensure_bucket(client, settings.MINIO_BUCKET_NAME)
            if course.file_key:
                remove_object_if_exists(
                    client,
                    settings.MINIO_BUCKET_NAME,
                    course.file_key,
                )
            client.put_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=file_key,
                data=uploaded.file,
                length=uploaded.size,
                content_type=uploaded.content_type,
            )
            file_url = client.presigned_get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=file_key,
                expires=timedelta(days=7),
            )
            file_url = normalize_clickable_url(file_url)
        except S3Error as exc:
            return Response(
                {"file": f"MinIO error: {exc.code}"},
                status=HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {"file": "Failed to upload file."},
                status=HTTP_502_BAD_GATEWAY,
            )

        course.file_key = file_key
        course.file_mime_type = uploaded.content_type
        course.original_file_name = uploaded.name
        course.save()
        return Response(
            {
                "course_name": course.title,
                "file_url": file_url,
            },
            status=HTTP_200_OK,
        )


class TaskFileUpload(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    # Ensures that task belongs to course that is owned by a teacher
    def owned_task(self, request, task_id):
        task = get_object_or_404(
            Task.objects.select_related('module__course'),
            id=task_id,
            module__course__teacher=request.user,
        )
        self.check_object_permissions(request, task)  # permissions won't run unless object-level checks run
        return task

    # Uploads to minIO
    def put(self, request, task_id, *args, **kwargs):
        task = self.owned_task(request, task_id)
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'file': 'This field is required.'}, status=HTTP_400_BAD_REQUEST)
        ext = os.path.splitext(uploaded.name)[1]
        file_key = f'tasks/{task.id}/{uuid.uuid4().hex}{ext}'

        client = get_minio_client()
        try:
            ensure_bucket(client, settings.MINIO_BUCKET_NAME)
            if task.file_key:
                remove_object_if_exists(
                    client,
                    settings.MINIO_BUCKET_NAME,
                    task.file_key,
                )
            client.put_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=file_key,
                data=uploaded.file,
                length=uploaded.size,
                content_type=uploaded.content_type,
            )
            file_url = client.presigned_get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=file_key,
                expires=timedelta(days=7),
            )
            file_url = normalize_clickable_url(file_url)
        except S3Error as exc:
            return Response(
                {"file": f"MinIO error: {exc.code}"},
                status=HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {"file": "Failed to upload file."},
                status=HTTP_502_BAD_GATEWAY,
            )
        task.file_key = file_key
        task.file_mime_type = uploaded.content_type
        task.file_size = uploaded.size
        task.original_file_name = uploaded.name
        task.save()
        return Response(
            {
                "task_name": task.title,
                "file_url": file_url,
            },
            status=HTTP_200_OK,
        )
    

class PublishCourse(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_course_and_validate(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, teacher=request.user)
        self.check_object_permissions(request, course)
        cant_publish = {}
        if course.file_key is None:
            cant_publish['cover']='Course cannot be published without a cover!'
       
        if not Module.objects.filter(course_id=course_id).exists():
            cant_publish['module'] = "Course cannot be published without modules!"
        
        tasks = Task.objects.filter(module__course_id=course_id)
        if not tasks.exists():
            cant_publish['tasks'] = "Course cannot be published without tasks!"

        
        if tasks.filter(file_key__isnull=True).exists():
            cant_publish['file'] = "Each task must have a file!"
        
        if cant_publish:
            raise ValidationError(cant_publish)
        else:
            return course
        
    def post(self, request, course_id, *args, **kwargs):
        course = self.get_course_and_validate(request, course_id)
        if course.status == Course.CourseStatus.PUBLISHED:
            return Response(
                {"detail": "Course is already published.", "status": course.status, "published_at": course.published_at},
                status=HTTP_200_OK,
            )
        course.status = Course.CourseStatus.PUBLISHED
        course.published_at = timezone.now()
        course.save(update_fields=["status", "published_at"])
        return Response(
            {"id": course.id, "status": course.status, "published_at": course.published_at},
            status=HTTP_200_OK,
        )
