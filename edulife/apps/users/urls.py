from django.urls import path, include
from apps.users.auth_views import forgot_password
from apps.users.auth_views import reset_password 
from apps.users.user_views import EditUserProfileAPIView,LookUserProfileAPIView,RegisterUserAPIView

urlpatterns = [
    path('forgot_password/', forgot_password.PasswordResetRequestAPIView.as_view(), name='forgot_password'), 
    path('reset_password/<str:token>/', reset_password.ResetPasswordAPIView.as_view(), name='reset_password'),
    path('edit_profile/', EditUserProfileAPIView.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='edit_profile'),
    path('my_profile/', LookUserProfileAPIView.as_view({'get':'retrieve'}), name='my_profile'),
    path('register/', RegisterUserAPIView.as_view(), name='register'),
]

