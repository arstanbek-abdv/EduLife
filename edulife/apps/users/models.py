from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'Студент', 'Student'
        TEACHER = 'Учитель', 'Teacher'
        ADMIN   = 'Админ',   'Admin'

    first_name = models.CharField(
        _('first name'),
        max_length=150,
        blank=False,
        null=False
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
    role = models.CharField(
        max_length=40,
        choices=Role.choices,
        default=Role.STUDENT,
        blank=False,
        null=False
    )
    bio = models.TextField(
        _('biography'),
        blank=True,
        default='',
        max_length=2000
    )
    profile_image = models.ImageField(
        upload_to='',
        blank=True,
        null=True,
    )
    file_key = models.CharField(max_length=512, blank=True, null=True) # permanent MinIO path
    file_mime_type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True) # size in bytes 
    
    password_reset_token = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="Одноразовый токен для сброса пароля (обычно 40–64 символа)"
    )
    password_reset_token_created = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Время создания токена — для проверки срока действия"
    )
    created_at = models.DateTimeField(
        _('date created'),
        default=timezone.now,
        editable=False,
        help_text="Дата и время создания аккаунта"
    )
    updated_at = models.DateTimeField(
        _('date updated'),
        auto_now=True,
        help_text="Дата и время последнего изменения профиля"
    )

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')