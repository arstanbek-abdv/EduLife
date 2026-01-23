from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models

# STORES ALL USERS!
class CustomUser(AbstractUser):

    class Role (models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'
        ADMIN = 'admin', 'Admin'

    # Overriding existing tables

    first_name = models.CharField(
        _('first name'),
        max_length=150, 
        blank=False, null=False
    )
    
    last_name = models.CharField(
        _('last name'),
        max_length=150,
        blank=False, 
        null=False
    )

    email = models.EmailField(
        _('email address'), 
        unique=True,
        blank=False,
        null=False,
    )

    # New fields
    role = models.CharField(
        max_length=40,
        choices=Role.choices,
        default=Role.STUDENT,
        blank=False,
        null=False
        )
    
    bio = models.TextField(
        _('biography'),
        blank = True, 
        default= '',
        max_length=2000,)
        
    profile_image = models.ImageField(
        upload_to='profile_pics/',
        blank = True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    
    def __str__(self):
        return f'{self.get_full_name()} {self.role}'


