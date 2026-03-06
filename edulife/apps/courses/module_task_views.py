from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from apps.courses.models import Module, Task
from apps.courses.serializers.course_serializers import ModuleSerializer, TaskSerializer
from apps.courses.permissions.course_permissions import IsEnrolled, IsAdmin

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для получения списка и деталей модулей.
    
    - list: Получить все модули (фильтр: ?course_id=X)
    - retrieve: Получить модуль по ID
    
    Фильтрация:
    - ?course_id=X — фильтр модулей по курсу
    """
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,IsAdmin]

    def get_queryset(self):
        queryset = Module.objects.select_related('course').all()
        
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.order_by('order')


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для получения списка и деталей заданий.
    
    - list: Получить все задания (фильтр: ?module_id=X или ?course_id=X)
    - retrieve: Получить задание по ID
    
    Фильтрация:
    - ?module_id=X — фильтр заданий по модулю
    - ?course_id=X — фильтр заданий по курсу (через модуль)
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,IsEnrolled,IsAdmin]

    def get_queryset(self):
        queryset = Task.objects.select_related('module__course').all()
        
        module_id = self.request.query_params.get('module_id')
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(module__course_id=course_id)
        
        return queryset
