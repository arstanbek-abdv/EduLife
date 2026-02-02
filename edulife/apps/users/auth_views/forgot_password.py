from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from edulife.settings import EMAIL_HOST_USER
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from apps.users.models import CustomUser
from django.utils.html import strip_tags


class PasswordResetRequestAPIView(APIView):
    permission_classes = (AllowAny, )

    def post(self, request):
        email = request.data.get("email", None)

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email, is_active=True)
        except CustomUser.DoesNotExist:
            return Response(
                {"message": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        token = get_random_string(48)
        user.password_reset_token = token
        user.password_reset_token_created = timezone.now()
        user.save(update_fields=['password_reset_token', 'password_reset_token_created'])

        domain = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        reset_url = f"{protocol}://{domain}/reset_password/{token}/" #TODO Здесь должна быть ссылка на форму сброса пароля на фронт

        context = {
            'user': user,
            'reset_url': reset_url,
            'year': timezone.now().year,
        }

        html_content = render_to_string('emails/password_reset.html', context)

        plain_content = strip_tags(html_content)

        try:
            send_mail(
                subject="Сброс пароля — Edulife",
                message=plain_content,
                from_email=EMAIL_HOST_USER,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False,
            )
        except Exception as e:
            return Response(
                {"error": "Не удалось отправить письмо. Попробуй позже."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "Письмо было успешно отправлено"},
            status=status.HTTP_200_OK
        )


