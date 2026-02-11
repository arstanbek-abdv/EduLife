from django.urls import path, include
from apps.courses.course_views import CreateCourseAPIView, UploadFileContent
urlpatterns = [
    path('create_courses/',CreateCourseAPIView.as_view()),
    path('tasks/<int:task_id>/upload/',UploadFileContent.as_view())
]