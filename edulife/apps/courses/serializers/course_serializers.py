from django.db import transaction 
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from apps.courses.models import Course, Module, Task

class TaskSerializer (ModelSerializer):
    class Meta:
        model = Task
        fields = ['title', 
                  'description', 
                  'task_type', 
                'file_content',
                'external_url'
                ]

class ModuleSerializer (ModelSerializer):
    tasks = TaskSerializer(many=True, source='task', required=True)
    class Meta:
        model = Module 
        fields = ['title',
                  'description',
                  'order',
                  'tasks' # virtual FK
                  ]

class CourseSerializer (ModelSerializer):
    module_to_course = ModuleSerializer(many=True, required=True)
    class Meta:
        model = Course
        fields = ['title',
                'description',
                'short_description', 
                'language',
                'cover_image',
                'category',
                'module_to_course' # virtual FK
                ]
        
    def create (self, validated_data):
        # Require modules to be provided; treat course creation as an atomic unit
        if 'module_to_course' not in validated_data:
            raise serializers.ValidationError({'module_to_course': 'Course must include at least one module.'})

        modules_data = validated_data.pop('module_to_course')
        # Inject teacher from request context
        teacher = self.context['request'].user

        with transaction.atomic():
            # Create Course row
            course = Course.objects.create(teacher=teacher, **validated_data)

            # Iterate over modules
            for module_data in modules_data:
                if 'task' not in module_data:
                    raise serializers.ValidationError({'task': 'Each module must include at least one task.'})

                tasks_data = module_data.pop('task')

                # Create Module row linked to Course
                module = Module.objects.create(course=course, **module_data)

                # Iterate over tasks
                for task_data in tasks_data:
                    # Create Task row linked to Module
                    Task.objects.create(module=module, **task_data)

        return course