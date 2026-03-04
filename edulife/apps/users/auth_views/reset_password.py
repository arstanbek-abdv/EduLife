from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjnagoValidationError
from rest_framework.exceptions import ValidationError 
from apps.users.models import CustomUser
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

class ResetPasswordAPIView(APIView):
    '''
    Сброс пароля по токену из письма.
    '''
    def post(self, request, token):
        password = request.data.get("password")
        if not password:
            return Response({'error':'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(password_reset_token=token)# Uses the token from the URL, looks it up in the database, returns a real user record 
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        try: 
            validate_password(password, user)
        except DjnagoValidationError as e:
            raise ValidationError({'password':e.messages})
        
        user.set_password(password)
        user.password_reset_token = None
        user.save()
        

        return Response({"message": "Password reset successful"})
