from django.contrib.auth.password_validation import validate_password
from django.core.files.storage import default_storage
from rest_framework import serializers

from apps.users.models import CustomUser

class EditProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name','role','username',
            'email', 'bio',
        ]
        read_only_fields = ['role']

class LookProfileSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()

    def get_profile_picture_url(self, obj):
        """
        Return a signed storage URL for the user's profile image, if it exists.
        """
        if not obj.file_key:
            return None
        try:
            return default_storage.url(obj.file_key)
        except Exception:
            return None

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'role','username',
            'email', 'bio', 'profile_picture_url'
        ]
  
class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name',
            'username', 'email', 'password'
        ]

        extra_kwargs = {
            'password': {'write_only': True}  # This hides it from the JSON response
        }
    # validate_password() must be overridden
    # DRF only runs validators that are wired into the serializer validation pipeline.

    def validate_password(self, value):
        validate_password(value, self.instance)
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')  # removes password from validated_data
        user = CustomUser(**validated_data)  # creates a new row fills remaining fields
        user.set_password(password)  # hashes password and puts hash to password field
        user.save()
        return user
