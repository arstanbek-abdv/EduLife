from django.urls import path, include
from apps.users.auth_views import forgot_password
from apps.users.auth_views import reset_password 
from apps.users.user_views import EditUserProfileView,LookUserProfileView

urlpatterns = [
    path('forgot_password/', forgot_password.PasswordResetRequestAPIView.as_view()), 
    path('reset_password/<str:token>/', reset_password.ResetPasswordAPIView.as_view()),
    path('edit_profile/', EditUserProfileView.as_view({'get': 'retrieve', 'patch': 'partial_update'})),
    path('my_profile/', LookUserProfileView.as_view({'get':'retrieve'})),
]

