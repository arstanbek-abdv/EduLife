from rest_framework import serializers
from apps.courses.models import CustomUser

class EditProfileSerializer (serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 
            'email', 'bio', 'profile_image']

class LookProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'role',
            'email', 'bio', 'profile_image'
        ]