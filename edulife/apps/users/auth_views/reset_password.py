from django.contrib.auth.tokens import default_token_generator
from apps.users.models import CustomUser
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.utils import timezone


class ResetPasswordAPIView(APIView):
    def post(self, request, token):

        password = request.data.get("password", None)

        if not password:
            return Response(
                {"error": "Введите пароль!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(password_reset_token=token)
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.password_reset_token = None
        user.save()

        return Response({"message": "Password reset successful"})
