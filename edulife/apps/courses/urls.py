from django.urls import path, include
from apps.courses.course_views import CreateCourseAPIView
urlpatterns = [
    path('create_courses/',CreateCourseAPIView.as_view()),
]