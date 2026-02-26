from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
    HTTP_409_CONFLICT,
    HTTP_502_BAD_GATEWAY,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.conf import settings
from django.shortcuts import get_object_or_404
from urllib.parse import urlparse
from minio import Minio
from minio.error import S3Error

from apps.users.models import CustomUser
from apps.courses.models import Course, Task, Enrollment, CompletedTask
from apps.courses.permissions.course_permissions import  IsEnrolled
from apps.courses.serializers.course_serializers import (
    TeacherCourseSerializer,
    StudentCourseSerializer,
    EnrollmentSerializer,
)

from apps.courses.utils import (
    get_minio_client,
    ensure_bucket,
    remove_object_if_exists,
    normalize_clickable_url,
)


class HomeAPIView(APIView):
    ''' 
    Returns all published courses for students (must be authenticated)
    and shows all teacher's courses draft/published.
    Allows to search for courses based on their title and category.

    For students the endpoint returns published courses containing basic 
    info about it, URL for cover image, URL to teacher's profile 
    who published the course, name and email, average rating.

    Teachers see all their courses/draft and published. average rating and enrollment count
    for published courses.
    '''
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        
        if user.role == CustomUser.Role.TEACHER:
            queryset = Course.objects.filter(teacher=user)
            category = request.query_params.get('category')
            title = request.query_params.get('title')
            
            if category:
                queryset = queryset.filter(category_id=category)
            if title:
                queryset = queryset.filter(title__icontains=title)
            serializer = TeacherCourseSerializer(queryset, many=True)
            return Response(serializer.data, status=HTTP_200_OK)
            
        elif user.role == CustomUser.Role.STUDENT:
            queryset = Course.objects.filter(enrollments__student=user).select_related('teacher').distinct()
            category = request.query_params.get('category')
            title = request.query_params.get('title')
            
            if category:
                queryset = queryset.filter(category_id=category)
            if title:
                queryset = queryset.filter(title__icontains=title)
            serializer = StudentCourseSerializer(queryset, many=True, context={'request': request})
            return Response(serializer.data, status=HTTP_200_OK)
        
        return Response({"detail": "Invalid user role"}, status=HTTP_403_FORBIDDEN)
    

class CourseCatalog (ModelViewSet):
    ''' 
    Returns all published courses for Unuathenticated users. 
    Passing course_id as query param allows to view a particular course.
    Allows to search courses based on categories
    '''
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = StudentCourseSerializer
    http_method_names = ['get']  # read-only

    def get_queryset(self):
        qs = Course.objects.filter(
            status=Course.CourseStatus.PUBLISHED
        ).select_related('teacher')

        category = self.request.query_params.get('category')
        title = self.request.query_params.get('title')

        if category:
            qs = qs.filter(category_id=category)
        if title:
            qs = qs.filter(title__icontains=title)

        return qs

class EnrollToCourseAPIView(APIView):
    ''' 
    This endpoint creates new enrollment record for a student and a course.
    If the student is already enrolled in a course, the endpoint will return 
    according message.
    '''
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
    ''' 
    Changes status field of enrollment record of a student and a course.
    '''
    permission_classes = [IsAuthenticated]
    def put(self,request,course_id,*args,**kwargs):
        enrollment = get_object_or_404(Enrollment,student=request.user, course=course_id)
        enrollment.status = Enrollment.Status.DROPPED
        enrollment.save()
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=HTTP_200_OK)


class TaskFileDownloadAPIView(APIView):
    ''' 
    Returns a short-lived URL of a task file which 
    belongs to the course. Only enrolled students for 
    the course can access this URL.
    '''
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
    '''
    Calculates the overall course progerss.
    Course total = (completed tasks/all tasks of a course)*100
    '''
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
