from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from apps.courses.models import Course, Module,Task, Enrollment

class EnrollmentSerializer(ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["id", "course", "status", "created_at"]
        read_only_fields = ["status", "created_at"]


class TaskSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = ['id','title','description', 'module']


class ModuleSerializer(ModelSerializer):
    class Meta:
        model = Module
        fields = ["id","course","title", "description", "order"]
        read_only_fields = ["course"]


class TeacherCourseSerializer(ModelSerializer):
    enrollment_count = serializers.SerializerMethodField()
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
            'enrollment_count'
        ]
    def get_enrollment_count(self,obj):
        count = Enrollment.objects.filter(course=obj).count()
        return count


class CourseSerializer(ModelSerializer):
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
        ]