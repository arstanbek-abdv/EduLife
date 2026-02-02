from rest_framework.permissions import BasePermission,DjangoModelPermissionsOrAnonReadOnly
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from apps.users.models import CustomUser
from apps.courses.models import Course 

