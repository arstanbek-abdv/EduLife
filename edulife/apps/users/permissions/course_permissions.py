from rest_framework.permissions import BasePermission
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.users.models import CustomUser
from apps.courses.models import Task
