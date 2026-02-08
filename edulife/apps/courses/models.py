from django.core.validators import FileExtensionValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from apps.users.models import CustomUser
from django.db import models

# STORES ALL CATEGORIES!
class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:                        # only generate if empty
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return 'Categories'
    

# STORES ALL COURSES!
class Course (models.Model):

    class CourseStatus (models.TextChoices):
        PUBLISHED = 'published', 'Published'
        DRAFT = 'draft', 'Draft'

    title = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.TextField()
    language = models.CharField(max_length=100)

    cover_image = models.ImageField(
        upload_to='cover_images/',
        blank = True,
        null = True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
# Each course is tied to one teacher. A teacher can have multiple courses
    teacher = models.ForeignKey( 
        CustomUser, 
        limit_choices_to={'role':CustomUser.Role.TEACHER},
        on_delete=models.SET_NULL,
        related_name='taught_courses',
        null=True,
        blank=True,  # Course can exist without teacher (temporarily/permanently)
        )
    
    category = models.ForeignKey(Category,
    on_delete=models.SET_NULL,
    null=True,blank=True,
    related_name='courses')

    status = models.CharField(max_length=20,default=CourseStatus.DRAFT)
    published_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title}'


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
        on_delete=models.PROTECT,
        limit_choices_to={'role': CustomUser.Role.STUDENT},
        related_name='enrollments',
        null = False,
        blank = False,
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
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

    def __str__(self):
        return f'Enrollments'


# STORES ALL MODULES!
class Module (models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
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

    def __str__(self):
        return f'Modules'


# STORES ALL TASKS!
class Task (models.Model):
    
    class TaskType (models.TextChoices):
        DOCUMENT = 'document', 'Document'
        VIDEO = 'video', 'Video'
        LINK = 'link', 'Link'

    title = models.CharField(max_length=200)
    description = models.TextField()
    module = models.ForeignKey(Module,on_delete=models.PROTECT, related_name='task')
    is_graded = models.BooleanField(default=False)
    weight = models.PositiveIntegerField(default=1,blank=True,null=True)

    max_attempts = models.PositiveSmallIntegerField(
        choices=[(1, "1 attempt"), (3, "3 attempts")],
        default=1, null=True, blank=False)
    
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.VIDEO)

    file_content = models.FileField(
        upload_to='file_content/',
        blank = True,
        null = True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc', 'pptx', 'ppt', 
        'xlsx', 'xls', 'zip', 'txt', 'rtf','png','jpg','jpeg'])])

    external_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Link to YouTube video or external resource URL")

    def __str__(self):
        return f'Tasks'


# STORES SUBMISSION HISTORY! EACH ATTEMPT IS GRADED!
class Submission (models.Model):

    student = models.ForeignKey(CustomUser, 
    limit_choices_to={'role': CustomUser.Role.STUDENT},
    on_delete=models.PROTECT, related_name='submissions')

    task = models.ForeignKey(Task,
    on_delete=models.PROTECT, 
    related_name='submissions')

    grade = models.PositiveIntegerField(null=True,blank=True)
    teacher_comment = models.TextField(null=True,blank=True)

    file = models.FileField(
        upload_to='submissions/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc', 'pptx', 'ppt', 
        'xlsx', 'xls','zip', 'txt', 'rtf','png','jpg','jpeg'])])
    student_comment = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta: #TODO Is this constraint needed in the first place?
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'task'],
                name='unique_submission_per_student_task'
            )
        ]
    
    def __str__(self):
        return f'Submissions'


# TRACKS PROGRESS! INDEPENDENT FROM GRADING! 
class TaskCompletion (models.Model):

    student = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        limit_choices_to={'role':CustomUser.Role.STUDENT}
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.PROTECT
    )

    status = models.BooleanField(default=False)

    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'task'],
                name='unique_completion_per_student_task'
            )
        ]


# STORES THE FINAL GRADE FOR EACH TASK! NECESSARY FOR COURSE GRADE COMPUTATION!
class GradeBook (models.Model):

    student = models.ForeignKey(
        CustomUser,
        limit_choices_to={'role':CustomUser.Role.STUDENT},
        on_delete=models.PROTECT
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.PROTECT
    )

    final_grade = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'task'],
                name='unique_final_grade_per_student_task'
            )
        ]

    
# STORES COURSE REVIEWS BY STUDENTS!
class Review (models.Model):
    student = models.ForeignKey(CustomUser,
    limit_choices_to={'role':CustomUser.Role.STUDENT},
    on_delete=models.PROTECT)
    
    course = models.ForeignKey(Course,
    on_delete=models.CASCADE) 

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
            models.Index(fields=['course', 'rating']),   # useful for avg rating queries
            models.Index(fields=['student']),
        ]


