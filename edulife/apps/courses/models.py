from django.core.validators import FileExtensionValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from apps.users.models import CustomUser
from django.db import models

"""
1. Написать везде verbose_name в каждом блять поле в каждой модельке

"""
class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="Slug")
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} {self.slug} {self.id}"
    

class Course(models.Model):
    class CourseStatus(models.TextChoices):
        PUBLISHED = 'published', 'Published'
        DRAFT = 'draft', 'Draft'

    title = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.TextField()
    language = models.CharField(max_length=20)

    cover_image = models.ImageField(
        upload_to='',
        blank = True,
        null = True,
    )
    original_file_name = models.CharField(max_length=255, blank=True, null=True)
    file_key = models.CharField(max_length=512, blank=True, null=True)
    file_mime_type = models.CharField(max_length=100, blank=True, null=True)
    teacher = models.ForeignKey(
        CustomUser, 
        limit_choices_to={'role':CustomUser.Role.TEACHER},
        on_delete=models.SET_NULL,
        related_name='teachers',
        null=True,
        blank=False
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='categories'
    )
    
    status = models.CharField(max_length=20, default=CourseStatus.DRAFT)
    creation_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.id} {self.title}'


class Module (models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name='modules'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

        indexes = [
            models.Index(fields=['course','order'])
        ]

        unique_together = [['course', 'order']]

    def __str__(self):
        return f'{self.title} {self.course}'


class Task (models.Model):
    class TaskType (models.TextChoices):
        DOCUMENT = 'document', 'Document'
        VIDEO = 'video', 'Video'
    title = models.CharField(max_length=200)
    description = models.TextField()
    module = models.ForeignKey(
        Module, 
        on_delete=models.PROTECT, 
        related_name='tasks'
    )
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.VIDEO)
    file_content = models.FileField(
        upload_to='',
        blank = True,
        null = True,
    )
    file_key = models.CharField(max_length=512, blank=True, null=True)
    file_mime_type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    original_file_name = models.CharField(max_length=255, blank=True, null=True)
    external_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="External resource URL"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id} {self.title} {self.module}'


class CompletedTask (models.Model):
    student = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        limit_choices_to={'role':CustomUser.Role.STUDENT},
        related_name='students'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.PROTECT,
        related_name='tasks'
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'task'],
                name='unique_completion_per_student_task'
            )
        ]

        #TODO нету __str__ метода



class Review (models.Model):
    student = models.ForeignKey(
        CustomUser,
        limit_choices_to={'role':CustomUser.Role.STUDENT},
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews'
    ) 
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), 
        MaxValueValidator(5)],
        blank=False,
        null=False
    )
    feedback = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course'],
                name='one_review_per_student_per_course'
            )
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'rating']),
            models.Index(fields=['student']),
        ]
    
    def __str__(self):
        return f'{self.student.get_full_name()} - {self.course.title} ({self.rating}/5)'


class Enrollment (models.Model):
    class Status (models.TextChoices):
        ACTIVE    = 'active',    'Active'
        COMPLETED = 'completed', 'Completed'
        DROPPED   = 'dropped',   'Dropped'
    status = models.CharField(max_length=20, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    student = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        limit_choices_to={'role': CustomUser.Role.STUDENT},
        related_name='enrollments',
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name='enrollments',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint( 
                fields=['student', 'course'],
                name='unique_student_course_enrollment',
            )
        ]

    def __str__(self):
        return f'{str(self.student)} {str(self.course.title)}'