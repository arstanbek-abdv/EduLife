from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.core.files.storage import default_storage
from django.urls import reverse

from apps.courses.models import Course, Module, Task, Enrollment, Review, CompletedTask, Category
from apps.users.models import CustomUser
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']

class TeacherBasicSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email', 'profile_url']

    def get_full_name(self, obj):
        return obj.get_full_name() if obj else None

    def get_profile_url(self, obj):
        if not obj:
            return None
        request = self.context.get('request')
        if not request:
            return None
        path = reverse('teacher_public_profile', kwargs={'pk': obj.pk})
        return request.build_absolute_uri(path)


class EnrollmentSerializer(ModelSerializer):
    class Meta:
        model = Enrollment
        fields = (
            "id", 
            "course", 
            "status", 
            "created_at"
        )
        read_only_fields = (
            "status", 
            "created_at"
        )


class ReviewSerializer(ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = (
            'id',
            'student',
            'student_name',
            'course',
            'rating',
            'feedback',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('student', 'created_at', 'updated_at')
    
    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.method == 'POST':
            student = request.user
            course = attrs.get('course')
            
            if not Enrollment.objects.filter(
                student=student,
                course=course,
                status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED]
            ).exists():
                raise serializers.ValidationError(
                    "You must be enrolled in this course to leave a review."
                )
            
            if Review.objects.filter(student=student, course=course).exists():
                raise serializers.ValidationError(
                    "You have already reviewed this course."
                )
        # Block edit after course publication
        if self.instance and self.instance.course.status == Course.CourseStatus.PUBLISHED:
            raise serializers.ValidationError(
                "Reviews cannot be edited after course publication."
            )
        
        return attrs


class TaskSerializer(ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id','title','description', 'module', 'file_url']
        read_only_fields = ['module']

    def get_file_url(self, obj):
        if not obj.file_key:
            return None
        try:
            return default_storage.url(obj.file_key)
        except Exception:
            return None
    
    def validate(self, attrs):
        module_id = self.context['view'].kwargs['module_id']
        request = self.context.get('request')
        user = request.user if request else None
        course = Course.objects.filter(modules=module_id, teacher=user).first()
        if not course:
            raise serializers.ValidationError(
                {'module': 'Module/course not found or access denied.'}
            )
        # only block creation when course is published; allow edits
        if self.instance is None and course.status == Course.CourseStatus.PUBLISHED:
            raise serializers.ValidationError(
                {'publication':'Cannot add tasks to published course'}
            )
        return attrs 
    
    
class ModuleSerializer(ModelSerializer):
    class Meta:
        model = Module
        fields = ["id","course","title", "description", "order"]
        read_only_fields = ['id',"course"]

    def validate(self, attrs):
        course_id = self.context['view'].kwargs['course_id']
        order = attrs.get('order')
        request = self.context.get('request')
        user = request.user if request else None
        course = Course.objects.filter(id=course_id, teacher=user).first()
        if not course:
            raise serializers.ValidationError({
                'course': 'Course not found or access denied.'
            })
        qs = Module.objects.filter(course_id=course_id, order=order)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({
                "order": "Module with this order already exists for this course."
            })
        # only block creation when course is published; allow edits
        if self.instance is None and course.status == Course.CourseStatus.PUBLISHED:
            raise serializers.ValidationError(
                {'publication':'Cannot add modules to published course.'}
            )
        return attrs

class TeacherCourseSerializer(ModelSerializer):
    enrollment_count = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Course 
        fields = [
            "id",
            "status",
            "category",
            "title",
            "language",
            "description",
            "short_description",
            'enrollment_count',
            'cover_url',
            'average_rating'
        ]

    def get_enrollment_count(self, obj):
        count = Enrollment.objects.filter(course=obj).count()
        return count

    def get_average_rating(self, obj):
        from django.db.models import Avg
        result = Review.objects.filter(course=obj).aggregate(Avg('rating'))
        avg = result['rating__avg']
        return round(avg, 2) if avg is not None else None

    def get_cover_url(self, obj):
        if not obj.file_key:
            return None
        try:
            return default_storage.url(obj.file_key)
        except Exception:
            return None

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.status == Course.CourseStatus.PUBLISHED:
            blocked = {'language','category'}
            changed = blocked.intersection(attrs.keys())
            if changed:
                raise serializers.ValidationError(
                    {field:'Cannot be changed after publication' for field in changed}
                )
        return attrs


class CatalogCourseSerializer(ModelSerializer):
    cover_url = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    teacher_info = TeacherBasicSerializer(source='teacher', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'status',
            'category',
            'title',
            'language',
            'description',
            'short_description',
            'cover_url',
            'average_rating',
            'teacher_info',
        ]
        read_only_fields = ['status', 'average_rating', 'teacher_info']
        
    def get_average_rating(self, obj):
        from django.db.models import Avg
        result = Review.objects.filter(course=obj).aggregate(Avg('rating'))
        avg = result['rating__avg']
        return round(avg, 2) if avg is not None else None

    def get_cover_url(self, obj):
        if not obj.file_key:
            return None
        try:
            return default_storage.url(obj.file_key)
        except Exception:
            return None


class StudentCourseSerializer(ModelSerializer):
    cover_url = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = [
            'id',
            'status',
            'category',
            'title',
            'language',
            'description',
            'short_description',
            'cover_url',
            'progress'
        ]
        read_only_fields = ['status', 'progress']

    def get_cover_url(self, obj):
        if not obj.file_key:
            return None
        try:
            return default_storage.url(obj.file_key)
        except Exception:
            return None

    def get_progress(self, obj):
        student = self.context['request'].user
        completed_tasks = CompletedTask.objects.filter(student=student,task__module__course=obj).count()
        all_tasks = Task.objects.filter(module__course=obj).count()
        result = (completed_tasks/all_tasks)*100
        return round(result)