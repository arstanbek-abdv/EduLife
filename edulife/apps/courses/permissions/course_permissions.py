from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.users.models import CustomUser
from apps.courses.models import Course, Task, Enrollment, Review

class IsTeacher(BasePermission):

    def has_permission(self, request, view):
        return request.user.role == CustomUser.Role.TEACHER


class IsTaskCourseTeacher(BasePermission):
    """
    Allows only the teacher who owns the task's course (for task file upload).
    Uses actual ownership instead of the role field, so course owners can upload
    even if role is misconfigured.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        task_id = view.kwargs.get('task_id')
        if not task_id:
            return False
        try:
            task = Task.objects.select_related('module__course').get(id=task_id)
            return task.module.course.teacher_id == request.user.pk
        except Task.DoesNotExist:
            return False


class IsEnrolled(BasePermission):
    """
    Universal permission to check if user is enrolled in a course.
    Works with Tasks (via task_id) and Reviews (via course_id or object).
    Safe methods (GET, HEAD, OPTIONS) are allowed for all authenticated users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow safe methods for all authenticated users
        if request.method in SAFE_METHODS:
            return True
        
        # For task-based views (TaskFileDownloadAPIView, ProgressCountAPIView)
        if 'task_id' in view.kwargs:
            task_id = view.kwargs['task_id']
            try:
                task = Task.objects.get(id=task_id)
                course = task.module.course
                enrollment = Enrollment.objects.get(
                    student=request.user,
                    course=course,
                    status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED]
                )
                return True
            except (Task.DoesNotExist, Enrollment.DoesNotExist):
                return False
        
        # For Review create action - check course_id from request data
        if view.action == 'create' and hasattr(view, 'action'):
            course_id = request.data.get('course')
            if not course_id:
                return False
            
            try:
                enrollment = Enrollment.objects.get(
                    student=request.user,
                    course_id=course_id,
                    status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED]
                )
                return True
            except Enrollment.DoesNotExist:
                return False
        
        return True

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow safe methods for all authenticated users
        if request.method in SAFE_METHODS:
            return True
        
        # For Review objects - check ownership and enrollment
        if isinstance(obj, Review):
            if obj.student != request.user:
                return False
            
            try:
                enrollment = Enrollment.objects.get(
                    student=request.user,
                    course=obj.course,
                    status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED]
                )
                return True
            except Enrollment.DoesNotExist:
                return False
        
        return True
    