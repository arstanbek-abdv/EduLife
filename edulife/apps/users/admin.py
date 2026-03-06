from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'role',
        'is_active',
    )
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)

    # Все важные поля сразу на главной странице — без табов
    fieldsets = (
        (None, {
            'fields': (
                'username',
                'password',
            )
        }),
        ('Личные данные', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'role',
            )
        }),
        ('О себе', {
            'fields': (
                'bio',
                'profile_image',
            ),
            'description': 'Upload profile picture in the Profile Image field below'
        }),
        ('MinIO файл (аватар)', {
            'fields': (
                'file_key',
                'original_file_name',
                'file_mime_type',
                'file_size',
            ),
            'classes': ('collapse',),
            'description': 'These fields are automatically populated when uploading via API'
        }),
        ('Сброс пароля', {
            'fields': (
                'password_reset_token',
                'password_reset_token_created',
            ),
            'classes': ('collapse',),  # можно свернуть, если мешает
        }),
        ('Права и статус', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Даты', {
            'fields': (
                'created_at',
                'updated_at',
                'last_login',
                'date_joined',
            ),
        }),
    )

    # Поля только для чтения (автоматические / системные)
    readonly_fields = (
        'created_at',
        'updated_at',
        'last_login',
        'date_joined',
        'password_reset_token_created',
        'file_key',
        'original_file_name',
        'file_mime_type',
        'file_size',
    )

    # При добавлении нового пользователя показываем только самое нужное
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'role',
                'is_staff',
                'is_active',
            ),
        }),
    )

    # Удобно фильтровать и искать по имени/фамилии
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    get_full_name.short_description = 'ФИО'