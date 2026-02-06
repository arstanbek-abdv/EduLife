from rest_framework.permissions import BasePermission
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.users.models import CustomUser
from apps.courses.models import Course

class IsTeacher (BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated: # we check wheter the user is authenticated
            return False
        # only then we check wheter the user is teacher 
        return request.user.role == CustomUser.Role.TEACHER
   