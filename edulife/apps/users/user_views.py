from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from apps.users.serializers.users_serializers import EditProfileSerializer,LookProfileSerializer
from apps.users.models import CustomUser

class EditUserProfileView (ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = EditProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']
    
    def get_object(self):
        return self.request.user

class LookUserProfileView (ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = LookProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def get_object(self):
        return self.request.user