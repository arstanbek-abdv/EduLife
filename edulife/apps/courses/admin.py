from django.contrib import admin
from apps.courses.models import Enrollment, Category, Course, Module, Task, Review, CompletedTask


class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1
    fields = ['title', 'description', 'order']


class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    fields = ['title', 'task_type', 'file_content', 'external_url']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'teacher', 'category', 'status', 'creation_time']
    list_filter = ['status', 'category', 'creation_time']
    search_fields = ['title', 'description', 'teacher__username']
    readonly_fields = ['creation_time', 'updated_time', 'published_at', 'file_key', 'original_file_name', 'file_mime_type']
    
    fieldsets = (
        ('Course Information', {
            'fields': ('title', 'description', 'short_description', 'language', 'category', 'teacher')
        }),
        ('Course Cover', {
            'fields': ('cover_image',),
            'description': 'Upload course cover image here'
        }),
        ('MinIO Storage (Read-only)', {
            'fields': ('file_key', 'original_file_name', 'file_mime_type'),
            'classes': ('collapse',),
            'description': 'These fields are automatically populated when uploading via API'
        }),
        ('Status', {
            'fields': ('status', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('creation_time', 'updated_time'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'course', 'order', 'created_at']
    list_filter = ['course', 'order', 'created_at']
    search_fields = ['title', 'course__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Module Information', {
            'fields': ('course', 'title', 'description', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'module', 'task_type', 'created_at']
    list_filter = ['task_type', 'module__course', 'created_at']
    search_fields = ['title', 'description', 'module__title']
    readonly_fields = ['created_at', 'updated_at', 'file_key', 'original_file_name', 'file_mime_type', 'file_size']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'module', 'task_type')
        }),
        ('File Upload', {
            'fields': ('file_content',),
            'description': 'Upload task file here'
        }),
        ('External Resource', {
            'fields': ('external_url',),
            'description': 'Or provide an external URL instead of uploading a file'
        }),
        ('MinIO Storage (Read-only)', {
            'fields': ('file_key', 'original_file_name', 'file_mime_type', 'file_size'),
            'classes': ('collapse',),
            'description': 'These fields are automatically populated when uploading via API'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug']
    search_fields = ['name', 'slug']
    readonly_fields = ['slug']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'course', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['student__username', 'course__title', 'feedback']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'course', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['student__username', 'course__title']


@admin.register(CompletedTask)
class CompletedTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'task', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['student__username', 'task__title']
