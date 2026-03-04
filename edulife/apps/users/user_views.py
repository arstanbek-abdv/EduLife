from django.core.files.storage import default_storage

from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_502_BAD_GATEWAY
from django.shortcuts import get_object_or_404

from apps.users.serializers.users_serializers import EditProfileSerializer, LookProfileSerializer
from apps.users.serializers.users_serializers import RegisterUserSerializer
from apps.users.models import CustomUser

import os
import uuid 

class EditUserProfileAPIView(ModelViewSet):
    ''' 
    Позволяет пользователям редактировать свой профиль.
    '''
    queryset = CustomUser.objects.all()
    serializer_class = EditProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["put", 'patch']
    
    def get_object(self):
        return self.request.user

class LookUserProfileAPIView(ModelViewSet):
    '''
    Позволяет пользователям просматривать свой профиль.
    '''
    queryset = CustomUser.objects.all()
    serializer_class = LookProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def get_object(self):
        return self.request.user


class TeacherPublicProfileAPIView(RetrieveAPIView):
    """Публичный профиль преподавателя; студенты могут просматривать по ID преподавателя."""
    permission_classes = [IsAuthenticated]
    serializer_class = LookProfileSerializer

    def get_object(self):
        teacher = get_object_or_404(CustomUser, pk=self.kwargs['pk'])
        if teacher.role != CustomUser.Role.TEACHER:
            raise NotFound()
        return teacher


class RegisterUserAPIView(CreateAPIView): 
    ''' 
    Регистрация пользователя. Обязательные поля: имя, фамилия,
    имя пользователя, email, пароль.
    '''
    permission_classes = [AllowAny]
    serializer_class = RegisterUserSerializer

class UploadUserProfile(APIView):
    ''' 
    Загрузка фото профиля пользователя.
    Максимальный размер 8 МБ.
    '''
    permission_classes = [IsAuthenticated]
    def patch (self,request):
        user = request.user
        self.check_object_permissions(request,user)
        # ↑ this line raises PermissionDenied / NotAuthenticated if forbidden
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'file': 'This field is required.'}, status=HTTP_400_BAD_REQUEST)

        # Basic size limit (adjust number to your needs)
        if uploaded.size > 8 * 1024 * 1024:  # 8 MB
            return Response({'file': 'File too large (max 8 MB)'}, status=HTTP_400_BAD_REQUEST)

        # Fix extension extraction
        _, ext = os.path.splitext(uploaded.name)
        if not ext:
            ext = '.jpg'  # fallback – better to reject if no extension

        file_key = f'profile_images/{uuid.uuid4().hex}{ext.lower()}'

        try:
            old_key = user.file_key

            default_storage.save(file_key, uploaded)

            if old_key:
                try:
                    default_storage.delete(old_key)
                except Exception:
                    pass

            file_url = default_storage.url(file_key)

        except Exception:
            return Response(
                {"file": "Failed to upload file"},
                status=HTTP_502_BAD_GATEWAY
            )

        # ─── Update DB only after everything succeeded ───
        user.file_key = file_key
        user.file_mime_type = uploaded.content_type or 'image/jpeg'
        user.original_file_name = uploaded.name[:255]
        user.save(update_fields=['file_key', 'file_mime_type', 'original_file_name'])

        return Response({
            "file_url": file_url,
            "detail": "Profile image updated"
        }, status=HTTP_200_OK) 