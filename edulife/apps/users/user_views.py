from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.users.serializers.users_serializers import EditProfileSerializer,LookProfileSerializer
from apps.users.serializers.users_serializers import RegisterUserSerializer
from apps.users.models import CustomUser

class EditUserProfileAPIView (ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = EditProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']
    
    def get_object(self):
        return self.request.user

class LookUserProfileAPIView (ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = LookProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def get_object(self):
        return self.request.user

class RegisterUserAPIView (CreateAPIView): 
    permission_classes = [AllowAny]
    serializer_class = RegisterUserSerializer




