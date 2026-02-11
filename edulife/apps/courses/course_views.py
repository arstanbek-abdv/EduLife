from rest_framework.views import APIView
from rest_framework.status import HTTP_400_BAD_REQUEST,HTTP_200_OK
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from apps.users.permissions.core_permissions import IsTeacher
from apps.courses.serializers.course_serializers import CourseSerializer
from apps.courses.models import Course, Task
from minio import Minio
import uuid 
import os 

client = Minio(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin123",
            secure=False
        )

class CreateCourseAPIView (CreateAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = CourseSerializer

class UploadFileContent (APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    # Ensures that task belongs to course that is owned by a teacher 
    def owned_task (self, request, task_id):
        task = get_object_or_404(Task.objects.select_related('module__course'),
            id = task_id,
            module__course__teacher = request.user)
        self.check_object_permissions(request,task) # permissions won't run unless object-level checks run
        return task 
    
    # Uploads to minIO
    def put (self, request, task_id, *args, **kwargs):
        task = self.owned_task(request,task_id)
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response ({'file':'This field is required.'}, status=HTTP_400_BAD_REQUEST)
        ext = os.path.splitext(uploaded.name)[1]
        file_key = f'tasks/{task.id}/{uuid.uuid4().hex}{ext}'
        
        if task.file_key:
            client.remove_object('edulife',task.file_key)

        client.put_object( 
            bucket_name='edulife',
            object_name=file_key,
            data=uploaded.file,
            length=uploaded.size,
            content_type=uploaded.content_type,
        )
        task.file_key = file_key
        task.file_mime_type = uploaded.content_type
        task.file_size = uploaded.size
        task.original_file_name = uploaded.name 
        task.save()
        return Response(
            {"task_name": task.title,
             "file_name": task.original_file_name,
             "file_size": task.file_size}, status=HTTP_200_OK
        )
    