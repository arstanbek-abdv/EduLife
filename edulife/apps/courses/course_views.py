from datetime import timedelta
import os
import uuid

from minio import Minio
from minio.error import S3Error

from rest_framework.views import APIView
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_502_BAD_GATEWAY,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.conf import settings
from django.shortcuts import get_object_or_404
from urllib.parse import urlparse

from apps.users.models import CustomUser
from apps.courses.models import Course, Task, Enrollment, CompletedTask
from apps.courses.permissions.course_permissions import IsTeacher, IsEnrolled
from apps.courses.serializers.course_serializers import (
    TeacherCourseSerializer,
    CourseSerializer,
    EnrollmentSerializer,
)

def get_minio_client():
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )


def ensure_bucket(client, bucket_name):
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)


def remove_object_if_exists(client, bucket_name, object_name):
    try:
        client.remove_object(bucket_name, object_name)
    except S3Error as exc:
        if exc.code not in {"NoSuchKey", "NoSuchObject"}:
            raise


def normalize_clickable_url(url: str) -> str:
    """
    Ensure URL is fully qualified (scheme + netloc), so UIs render it clickable.
    """
    if not url:
        return url
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return url
    scheme = "https" if getattr(settings, "MINIO_USE_SSL", False) else "http"
    endpoint = getattr(settings, "MINIO_ENDPOINT", "").strip().lstrip("/")
    # If MinIO already returned a path-only URL, keep it.
    path = url if url.startswith("/") else f"/{url}"
    if endpoint:
        return f"{scheme}://{endpoint}{path}"
    return f"{scheme}://{path.lstrip('/')}"

class HomeAPIView(APIView):
    def get (self,request):
        user = request.user
        if user.role == CustomUser.Role.TEACHER:
            teacher_courses = Course.objects.filter(teacher=user)
            serializer = TeacherCourseSerializer(teacher_courses,many=True)
            return Response(serializer.data, status=HTTP_200_OK)
        elif user.role == CustomUser.Role.STUDENT:
            published_courses = Course.objects.filter(status=Course.CourseStatus.PUBLISHED)
            serializer = CourseSerializer(published_courses,many=True)
            return Response(serializer.data, status=HTTP_200_OK)
        
class CourseCatalog (ModelViewSet):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = CourseSerializer

    def get_queryset(self):
        if self.request.user.is_anonymous or self.request.user.role == CustomUser.Role.STUDENT:
            return Course.objects.filter(status=Course.CourseStatus.PUBLISHED)
     

class EnrollToCourseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id, *args, **kwargs):
        if request.user.role != CustomUser.Role.STUDENT:
            return Response(
                {"detail": "Only students can enroll in courses."},
                status=HTTP_403_FORBIDDEN,
            )
        course = get_object_or_404(Course, id=course_id)
        if course.status != Course.CourseStatus.PUBLISHED:
            return Response(
                {"detail": "Only published courses can be enrolled in."},
                status=HTTP_400_BAD_REQUEST,
            )
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course= course,
            defaults={"status": Enrollment.Status.ACTIVE},
        )
        if not created:
            if enrollment.status in (Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED):
                return Response(
                    {"detail": "Already enrolled in this course."},
                    status=HTTP_409_CONFLICT,
                )
            enrollment.status = Enrollment.Status.ACTIVE
            enrollment.save(update_fields=["status"])
        return Response(EnrollmentSerializer(enrollment).data, status=HTTP_200_OK)
    

class UnenrollCourseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self,request,course_id,*args,**kwargs):
        enrollment = get_object_or_404(Enrollment,student=request.user, course=course_id)
        enrollment.status = Enrollment.Status.DROPPED
        enrollment.save()
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=HTTP_200_OK)


class TaskFileDownloadAPIView(APIView):
    """Return a short-lived presigned URL for a task file. Teacher-owner or enrolled students only."""
    permission_classes = [IsAuthenticated,IsEnrolled]
    def get(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(
            Task.objects.select_related("module__course"),
            id=task_id,
        )
        client = get_minio_client()
        try:
            file_url = client.presigned_get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=task.file_key,
                expires=timedelta(minutes=15),
            )
            file_url = normalize_clickable_url(file_url)
        except Exception:
            return Response(
                {"detail": "Failed to generate download URL."},
                status=HTTP_502_BAD_GATEWAY,
            )
        return Response({"url": file_url}, status=HTTP_200_OK)

class ProgressCountAPIView(APIView):
    permission_classes = [IsAuthenticated,IsEnrolled]
    def post (self, request, task_id):
        done_task = CompletedTask.objects
        student = request.user
        task = Task.objects.get(id=task_id)
        if done_task.filter(student=student,task=task_id).exists():
            return Response('You already completed this task', status=HTTP_200_OK)
        new_task = CompletedTask()
        new_task.task = task
        new_task.student = student
        new_task.save()
        course = task.module.course
        all_tasks_of_course = Task.objects.filter(module__course = course).count()
        completed_tasks = CompletedTask.objects.filter(student=student,task__module__course = course).count()
        progress = (completed_tasks/all_tasks_of_course) * 100
        return Response({'progress':progress}, status=HTTP_200_OK)
