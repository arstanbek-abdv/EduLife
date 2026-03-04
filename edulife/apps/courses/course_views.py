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
from apps.users.models import CustomUser
from apps.courses.models import Course, Task, Enrollment, CompletedTask
from apps.courses.permissions.course_permissions import IsEnrolled
from apps.courses.serializers.course_serializers import (
    TeacherCourseSerializer,
    CatalogCourseSerializer,
    EnrollmentSerializer,
    StudentCourseSerializer
)

from apps.courses.utils import (
    get_minio_client,
    normalize_clickable_url,
)


class HomeAPIView(APIView):
    ''' 
    Возвращает опубликованные курсы для студентов (требуется аутентификация)
    и показывает все курсы преподавателя в черновике и опубликованные.
    Позволяет искать курсы по названию и категории.

    Для студентов: для каждого студента возвращает свои курсы, прогресс курса, обложка

    Преподаватели видят все свои курсы (черновики и опубликованные),
    средний рейтинг и количество записей для опубликованных курсов.
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
            queryset = Course.objects.filter(courses__student=user).select_related('teacher').distinct()
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
    Возвращает все опубликованные курсы для неаутентифицированных пользователей.
    Передача course_id в качестве параметра запроса позволяет просмотреть конкретный курс.
    Позволяет искать курсы по категориям.
    '''
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = CatalogCourseSerializer
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
    Создаёт запись о записи студента на курс.
    Если студент уже записан на курс, возвращается соответствующее сообщение.
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
    Изменяет статус записи студента на курс (отмена записи).
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
    Возвращает кратковременный URL файла задания курса.
    Доступ к URL имеют только студенты, записанные на курс.
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

class CompleteTaskAPIView(APIView):
    ''' 
    Отмечает задание как выполненное студентом.
    '''
    permission_classes = [IsAuthenticated,IsEnrolled]
    def post (self, request, task_id):
        done_task = CompletedTask.objects
        student = request.user
        task = Task.objects.get(id=task_id)
        if done_task.filter(student=student,task=task_id).exists():
            return Response({'detail':'You already completed this task'}, status=HTTP_200_OK)
        new_task = CompletedTask()
        new_task.task = task
        new_task.student = student
        new_task.save()
        return Response({'detail':'Task completed'}, status=HTTP_200_OK)
        