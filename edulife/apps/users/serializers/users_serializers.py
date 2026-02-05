from rest_framework import serializers
from apps.courses.models import CustomUser

class EditProfileSerializer (serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'username',
            'email', 'bio', 'profile_image'
        ]

class LookProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'role',
            'email', 'bio', 'profile_image'
        ]

class RegisterUserSerializer (serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 
            'username','email', 'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True} # This hides it from the JSON response
        }

    def create (self, validated_data):
        password = validated_data.pop('password') #removes password from automatic validated_data variable to password variable
        user = CustomUser(**validated_data) # creates a new row fills remaining fields
        user.set_password(password) # hashes password and puts hash to password field 
        user.save()
        return user 
    