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


class CourseOutlineSerializer(ModelSerializer):
    """Course with modules and task outline only (id, title, task_type)."""
    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "status",
            "description",
            "short_description",
            "language",
            "category",
        ]
        read_only_fields = [
            "id",
            "title",
            "status",
            "description",
            "short_description",
            "language",
            "category",
        ]


class TeacherCourseSerializer(ModelSerializer):
    enrolled_count = serializers.SerializerMethodField()

    def get_enrolled_count(self, obj):
        return getattr(obj, "enrolled_count", None)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "status",
            "description",
            "short_description",
            "language",
            "category",
            "enrolled_count",
        ]
        read_only_fields = [
            "id",
            "title",
            "status",
            "description",
            "short_description",
            "language",
            "category",
            "enrolled_count"
            ]


class CreateCourseSerializer(ModelSerializer):
    class Meta:
        model = Course 
        fields = [
            "id",
            "title",
            "status",
            "description",
            "short_description",
            "language",
            "category",
        ]


