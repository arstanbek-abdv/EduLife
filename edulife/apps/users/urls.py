from django.urls import path, include
from apps.users.auth_views import forgot_password
from apps.users.auth_views import reset_password
from apps.users.user_views import (
    EditUserProfileAPIView,
    LookUserProfileAPIView,
    RegisterUserAPIView,
    TeacherPublicProfileAPIView,
)
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('login/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', jwt_views.TokenBlacklistView.as_view(), name='logout'),
    path('forgot-password/', forgot_password.PasswordResetRequestAPIView.as_view(), name='forgot_password'),
    path('reset-password/<str:token>/', reset_password.ResetPasswordAPIView.as_view(), name='reset_password'),
    path('edit-profile/', EditUserProfileAPIView.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='edit_profile'),
    path('my-profile/', LookUserProfileAPIView.as_view({'get': 'retrieve'}), name='my_profile'),
    path('teacher-profiles/<int:pk>/', TeacherPublicProfileAPIView.as_view(), name='teacher_public_profile'),
    path('register/', RegisterUserAPIView.as_view(), name='register'),
]

