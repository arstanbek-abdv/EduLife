from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from apps.courses.models import Module, Task
from apps.courses.serializers.course_serializers import ModuleSerializer, TaskSerializer
from apps.courses.permissions.course_permissions import IsEnrolled

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving modules.
    
    - list: Get all modules (filter by ?course_id=X)
    - retrieve: Get a specific module by ID
    
    Filtering:
    - ?course_id=X - filter modules by course
    """
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Module.objects.select_related('course').all()
        
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.order_by('order')


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving tasks.
    
    - list: Get all tasks (filter by ?module_id=X or ?course_id=X)
    - retrieve: Get a specific task by ID
    
    Filtering:
    - ?module_id=X - filter tasks by module
    - ?course_id=X - filter tasks by course (via module)
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,IsEnrolled]

    def get_queryset(self):
        queryset = Task.objects.select_related('module__course').all()
        
        module_id = self.request.query_params.get('module_id')
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(module__course_id=course_id)
        
        return queryset
