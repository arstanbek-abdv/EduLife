from django.core.validators import FileExtensionValidator
from users.models import CustomUser
from django.db import models

# STORES ALL COURSES!
class Course (models.Model):

    title = models.CharField(max_length=200)
    description = models.TextField()
    prerequisites = models.TextField()
    language = models.CharField(max_length=100)
    is_published = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cover_image = models.ImageField(
        upload_to='cover_images/',
        blank = True,
        null = True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    teacher = models.ForeignKey(
        CustomUser,
        limit_choices_to={'role':CustomUser.Role.TEACHER},
        on_delete=models.SET_NULL,
        related_name='taught_courses',
        null=True,
        blank=True,  # Course can exist without teacher (temporarily/permanently)
        )



# STORES ALL ENROLLMENTS 
class Enrollment (models.Model):

    class Status (models.TextChoices):
        ACTIVE    = 'active',    'Active'
        COMPLETED = 'completed', 'Completed'
        DROPPED   = 'dropped',   'Dropped'

    status = models.CharField(max_length=20,default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': CustomUser.Role.STUDENT},
        related_name='enrollments',
        null = False,
        blank = False,
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        null = False,
        blank = False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint( 
            fields=['student', 'course'],
            name='unique_student_course_enrollment',
        )
        ]


# STORES ALL MODULES!
class Module (models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='module_to_course'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

        indexes = [
            models.Index(fields=['course','order'])
        ]

        unique_together = [['course', 'order']]


# STORES ALL LESSONS!
class Lesson (models.Model):

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lesson_to_module',
    )
    minutes = models.IntegerField(default=15)
    created_at = models.DateTimeField(auto_now_add=True)


