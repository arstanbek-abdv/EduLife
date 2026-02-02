from django.urls import path, include
from apps.users.auth_views import forgot_password
from apps.users.auth_views import reset_password 

urlpatterns = [
    path('forgot_password/', forgot_password.PasswordResetRequestAPIView.as_view()), 
    path('reset_password/<str:token>/', reset_password.ResetPasswordAPIView.as_view()),
]

