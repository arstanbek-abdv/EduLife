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
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from urllib.parse import urlparse

from apps.users.models import CustomUser
from apps.courses.models import Course, Task, Enrollment, CompletedTask
from apps.courses.permissions.course_permissions import IsTeacher, IsEnrolled
from apps.courses.serializers.course_serializers import (
    CourseSerializer,
    CourseOutlineSerializer,
    EnrollmentSerializer,
    CompletedTaskSerializer
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

class CourseAPIView(ReadOnlyModelViewSet):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsTeacher()]

    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.Role.TEACHER:
            return (
                Course.objects.filter(teacher=user)
                .annotate(
                    enrolled_count=Count(
                        "enrollments",
                        filter=Q(
                            enrollments__status__in=[
                                Enrollment.Status.ACTIVE,
                                Enrollment.Status.COMPLETED,
                            ]
                        ),
                    )
                )
            )
        if user.role == CustomUser.Role.STUDENT:
            return Course.objects.filter(status=Course.CourseStatus.PUBLISHED)
        
    def _is_teacher_owner_or_enrolled(self, request, course):
        if course.teacher_id == request.user.id:
            return True
        return Enrollment.objects.filter(
            student=request.user,
            course=course,
            status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
        ).exists()

    def get_serializer_class(self):
        if self.action == "list":
            if self.request.user.role == CustomUser.Role.TEACHER:
                return CourseSerializer
            return CourseOutlineSerializer
        return CourseOutlineSerializer  # default for retrieve; overridden below

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == CustomUser.Role.TEACHER:
            serializer = CourseSerializer(instance, context={"request": request})
        elif self._is_teacher_owner_or_enrolled(request, instance):
            serializer = CourseSerializer(instance, context={"request": request})
        else:
            serializer = CourseOutlineSerializer(instance, context={"request": request})
        return Response(serializer.data)

class CourseCatalog (ModelViewSet):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = CourseOutlineSerializer

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

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(
            Task.objects.select_related("module__course"),
            id=task_id,
        )
        course = task.module.course
        if request.user.role == CustomUser.Role.TEACHER:
            if course.teacher_id != request.user.id:
                return Response(
                    {"detail": "You do not have access to this task file."},
                    status=HTTP_403_FORBIDDEN,
                )
        elif request.user.role == CustomUser.Role.STUDENT:
            if not Enrollment.objects.filter(
                student=request.user,
                course=course,
                status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
            ).exists():
                return Response(
                    {"detail": "You must be enrolled in this course to access task files."},
                    status=HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                {"detail": "Access denied."},
                status=HTTP_403_FORBIDDEN,
            )
        if not task.file_key:
            return Response(
                {"detail": "This task has no file."},
                status=HTTP_404_NOT_FOUND,
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
        new_task = CompletedTask()
        student = request.user
        task = Task.objects.get(id=task_id)
        new_task.task = task
        new_task.student = student
        new_task.save()
        course = task.module.course
        all_tasks_of_course = Task.objects.filter(module__course = course).count()
        completed_tasks = CompletedTask.objects.filter(student=student,task__module__course = course).count()
        progress = (completed_tasks/all_tasks_of_course) * 100
        return Response({'progress':progress}, status=HTTP_200_OK)
