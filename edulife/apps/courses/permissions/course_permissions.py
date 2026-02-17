from rest_framework.permissions import BasePermission
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.users.models import CustomUser
from apps.courses.models import Course, Task, Enrollment 

class IsTeacher (BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated: 
            return False
        return request.user.role == CustomUser.Role.TEACHER

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated: 
            return False
        # Direct course check
        if isinstance(obj, Course):
            return obj.teacher_id == request.user.id
        # Task is owned via its module's course
        if isinstance(obj, Task):
            return obj.module.course.teacher_id == request.user.id
        # Fallback: try generic teacher_id attribute if present
        teacher_id = getattr(obj, "teacher_id", None)
        return teacher_id == request.user.id

class IsEnrolled(BasePermission):
    def has_permission(self, request, view):
        task_id = view.kwargs['task_id']
        student = request.user
        try:
            task = Task.objects.get(id=task_id)
            course = task.module.course
            enrollment = Enrollment.objects.get(student=student,course=course)
            if enrollment.status == 'active' or enrollment.status == 'completed':
                return True
            else:
                return False
        except Enrollment.DoesNotExist:
            return False