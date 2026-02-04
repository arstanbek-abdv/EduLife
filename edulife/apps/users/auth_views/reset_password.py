from django.contrib.auth.tokens import default_token_generator
from apps.users.models import CustomUser
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

def password_validator(password, username, email):
    errors = {}
    pw = "" if password is None else str(password)
    pw_lower = pw.lower()

    if len(pw) < 12:
        errors['length'] = 'Must contain at least 12 characters'

    if not any(c.isupper() for c in pw):
        errors['uppercase'] = 'Must contain at least one uppercase'

    if not any(c.islower() for c in pw):
        errors['lowercase'] = 'Must contain at least one lowercase'

    if not any(c.isdigit() for c in pw):
        errors['digit'] = 'Must contain at least one digit'

    # Simple similarity checks (case-insensitive substring checks)
    if username:
        username_lower = str(username).lower().strip()
        if username_lower in pw_lower:
            errors['similar_to_username'] = 'Password contains parts of your username'

    if email:
        email_local = str(email).lower().strip().split('@')[0]
        if email_local in pw_lower:
            errors['similar_to_email'] = 'Password contains parts of your email'

    return errors if errors else None

class ResetPasswordAPIView(APIView):
    def post(self, request, token):
        password = request.data.get("password")
        if password is None or not password.strip():
            return Response({'error':'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(password_reset_token=token)# Uses the token from the URL, looks it up in the database, returns a real user record 
            email = user.email
            username = user.username
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate against the actual user found by token (username/email may not be sent in request)
        errors = password_validator(password, username, email)
        if errors:
            return Response(errors,status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(password)
        user.password_reset_token = None
        user.save()

        return Response({"message": "Password reset successful"})
