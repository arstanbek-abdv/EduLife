from django.db import transaction
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from apps.courses.models import Course, Module, Task, Enrollment


class EnrollmentSerializer(ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["id", "course", "status", "created_at"]
        read_only_fields = ["status", "created_at"]


class TaskOutlineSerializer(ModelSerializer):
    """Minimal task fields for unenrolled students (outline view)."""

    class Meta:
        model = Task
        fields = ["id", "title", "task_type"]
        read_only_fields = ["id", "title", "task_type"]


class TaskSerializer(ModelSerializer):

    class Meta:
        model = Task
        fields = [
            "id",
            "module",
            "title",
            "description",
            "task_type",
            "external_url",
        ]
        read_only_fields = ["module"]

class ModuleOutlineSerializer(ModelSerializer):
    tasks = TaskOutlineSerializer(many=True, source="task", read_only=True)

    class Meta:
        model = Module
        fields = ["id", "title", "description", "order", "tasks"]
        read_only_fields = ["id", "title", "description", "order", "tasks"]


class ModuleSerializer(ModelSerializer):

    class Meta:
        model = Module
        fields = ["id","course","title", "description", "order"]
        read_only_fields = ["course"]

class CourseOutlineSerializer(ModelSerializer):
    """Course with modules and task outline only (id, title, task_type). For unenrolled students."""

    modules = ModuleOutlineSerializer(many=True, read_only=True)
    
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
            "modules",
        ]
        read_only_fields = [
            "id",
            "title",
            "status",
            "description",
            "short_description",
            "language",
            "category",
            "modules",
        ]


class CourseSerializer(ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
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
            "modules",
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
            "modules",
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