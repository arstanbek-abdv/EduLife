from apps.courses.models import Course,Module,Task
from apps.users.models import CustomUser
from apps.courses.permissions.course_permissions import IsTeacher, IsTaskCourseTeacher, IsAdmin, IsTeacherOrAdmin
from django.shortcuts import get_object_or_404
from apps.courses.serializers.course_serializers import (
    ModuleSerializer,
    TaskSerializer,
    TeacherCourseSerializer,
    CatalogCourseSerializer
)
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied

from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_502_BAD_GATEWAY,
    HTTP_409_CONFLICT,
    HTTP_204_NO_CONTENT
)
from django.core.files.storage import default_storage
from django.utils import timezone
import uuid
import os

from edulife.settings import DATA_UPLOAD_MAX_MEMORY_SIZE

class CreateEditCourse(ModelViewSet):
    ''' 
    Только преподаватели могут создавать курсы.
    Курс включает краткое описание и основную информацию,
    созданные курсы по умолчанию в черновике.
    Только администратор и преподаватели могут редактировать черновики курсов.
    Курс может содержать несколько модулей, модуль — несколько заданий.
    Каждое задание должно содержать прикреплённый файл.
    '''
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    serializer_class = TeacherCourseSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.Role.ADMIN:
            return Course.objects.all()
        return Course.objects.filter(teacher=user)
    
    def perform_create(self, serializer):
        return serializer.save(teacher=self.request.user)
    
    def perform_destroy(self, instance):
        if instance.status == Course.CourseStatus.PUBLISHED:
            raise PermissionDenied('Published courses cannot be deleted.')
        instance.delete()


class CreateEditModule(ModelViewSet):
    ''' 
    Модуль не может существовать отдельно от курса.
    Каждый модуль должен ссылаться на курс.
    '''
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    serializer_class = ModuleSerializer
    http_method_names = ['post','patch','delete']
    
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        user = self.request.user
        modules = Module.objects.filter(course=course_id)
        if user.role != CustomUser.Role.ADMIN:
            modules = modules.filter(course__teacher=user)
        return modules
        
    def perform_create(self, serializer):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, id=course_id)
        return serializer.save(course=course)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.course.status == Course.CourseStatus.PUBLISHED:
            return Response(
                {"detail": "Modules of published courses cannot be deleted."},
                status=HTTP_400_BAD_REQUEST
            )
        if instance.tasks.exists():
            return Response(
                {"detail": "Delete tasks first."},
                status=HTTP_409_CONFLICT
            )
        
        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)
        
class CreateEditTask(ModelViewSet):
    '''
    Так же, как модуль не может существовать без курса,
    задание не может существовать без модуля — каждое задание должно ссылаться на модуль.
    '''
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    serializer_class = TaskSerializer
    http_method_names = ['post','patch','delete']

    def get_queryset(self):
        module_id = self.kwargs['module_id']
        user = self.request.user
        tasks = Task.objects.filter(module=module_id)
        if user.role != CustomUser.Role.ADMIN:
            tasks = tasks.filter(module__course__teacher=user)
        return tasks 

    def perform_create(self, serializer):
        module_id = self.kwargs['module_id']
        module = get_object_or_404(Module,id=module_id)
        return serializer.save(module=module)

    def perform_destroy(self, instance):
        if instance.module.course.status == Course.CourseStatus.PUBLISHED:
            raise PermissionDenied('Tasks of published courses cannot be deleted.')
        instance.delete()


class CourseCoverUpload(APIView):
    ''' 
    Загрузка обложки курса.
    Если курс не найден или endpoint вызван посторонним, возвращается ошибка 404.
    Возвращает URL для просмотра изображения.
    '''
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def course_teacher(self, request, course_id):
        user = request.user
        if user.role == CustomUser.Role.ADMIN:
            course = get_object_or_404(Course, id=course_id)
        else:
            course = get_object_or_404(Course, id=course_id, teacher=user)
        self.check_object_permissions(request, course)
        return course

    def put(self, request, course_id, *args, **kwargs):
        course = self.course_teacher(request, course_id)
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'file': 'This field is required.'}, status=HTTP_400_BAD_REQUEST)
        ext = os.path.splitext(uploaded.name)[1]
        file_key = f'course_covers/{course.id}/{uuid.uuid4().hex}{ext}'

        try:
            if course.file_key:
                try:
                    default_storage.delete(course.file_key)
                except Exception:
                    pass
            default_storage.save(file_key, uploaded)
            file_url = default_storage.url(file_key)
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
    '''
    Only the course teacher can upload a file for a task.
    Admins can upload files for any task.
    '''
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def owned_task(self, request, task_id):
        user = request.user
        task = get_object_or_404(
            Task.objects.select_related('module__course'),
            id=task_id,
        )
        if user.role != CustomUser.Role.ADMIN and task.module.course.teacher_id != user.id:
            raise PermissionDenied('You do not have permission to upload files for this task.')
        self.check_object_permissions(request, task)
        return task

    def put(self, request, task_id, *args, **kwargs):
        task = self.owned_task(request, task_id)
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'file': 'This field is required.'}, status=HTTP_400_BAD_REQUEST)
        ext = os.path.splitext(uploaded.name)[1]
        file_key = f'tasks/{task.id}/{uuid.uuid4().hex}{ext}'

        if uploaded.size > DATA_UPLOAD_MAX_MEMORY_SIZE:
            return Response({'file': 'File too large (max 2 GB)'}, status=HTTP_400_BAD_REQUEST)

        try:
            if task.file_key:
                try:
                    default_storage.delete(task.file_key)
                except Exception:
                    pass
            default_storage.save(file_key, uploaded)
            file_url = default_storage.url(file_key)
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
    ''' 
    Перед публикацией курса проверяется его целостность.
    Курс должен содержать: обложку, минимум один модуль.
    Каждый модуль — минимум одно задание с прикреплённым файлом.
    При несоответствии требованиям возвращается сообщение об ошибке.
    Пример: cover: Курс не может быть опубликован без обложки!
    Если курс не найден, возвращается ошибка 404.
    '''
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def get_course_and_validate(self, request, course_id):
        user = request.user
        if user.role == CustomUser.Role.ADMIN:
            course = get_object_or_404(Course, id=course_id)
        else:
            course = get_object_or_404(Course, id=course_id, teacher=user)
        self.check_object_permissions(request, course)
        cant_publish = {}
        if course.file_key is None:
            cant_publish['cover'] = 'Course cannot be published without a cover!'
       
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
        
    def patch(self, request, course_id, *args, **kwargs):
        user = request.user
        if user.role == CustomUser.Role.ADMIN:
            course = get_object_or_404(Course, id=course_id)
        else:
            course = get_object_or_404(Course, id=course_id, teacher=user)
        if course.status == Course.CourseStatus.PUBLISHED:
            return Response(
                {"detail": "Course is already published.", "status": course.status, "published_at": course.published_at},
                status=HTTP_400_BAD_REQUEST,
            )
        course = self.get_course_and_validate(request, course_id)
        course.status = Course.CourseStatus.PUBLISHED
        course.published_at = timezone.now()
        course.save(update_fields=["status", "published_at"])
        course = Course.objects.select_related('teacher').get(pk=course.pk)
        serializer = CatalogCourseSerializer(course, context={'request': request})
        return Response(
            serializer.data,
            status=HTTP_200_OK,
        )
    
   #TODO Псмотреть бест практисы по респонсам по типу: 
        """
        {
            "message": "Task creation error",
            "errors": [
                {
                    "field": "file",
                    "code": "required",
                    "message": "Task must include file"
                },
            ]
        }
        """