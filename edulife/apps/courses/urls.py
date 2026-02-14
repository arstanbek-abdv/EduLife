from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.courses.course_views import (
    CourseCatalog,
    CourseAPIView,
    CourseCoverUpload,
    TaskFileUpload,
    PublishCourse,
    CourseEnrollmentAPIView,
    TaskFileDownloadAPIView,
)
from apps.courses.course_creation import (
    CreateCourseAPIView,
    CreateModuleAPIView,
    CreateTaskAPIView 
    )

router = DefaultRouter()
# This app is mounted at `/api/courses/` in the project urls,
# so keep route prefixes here *relative* (avoid `/courses/courses/...`).

router.register(r"", CourseAPIView, basename="all-courses")
# Endpoint above is for creating a course structure
# TODO make this endpoint only for viewing, separate endpoints for course,module and task creation is necessary!

# As teacher for viewing owned courses and number of enrolled students in each course
# As student for viewing all the published courses and their descriptions (no task files available)
urlpatterns = [
    path('catalog/', CourseCatalog.as_view({'get': 'list'})),
    path('catalog/<int:pk>/', CourseCatalog.as_view({'get': 'retrieve'})),
    path('courses/', CreateCourseAPIView.as_view()),
    path('courses/<int:course_id>/modules/', CreateModuleAPIView.as_view()),
    path('modules/<int:module_id>/tasks/',CreateTaskAPIView.as_view()),
    path("tasks/<int:task_id>/upload/", TaskFileUpload.as_view()),
    path("tasks/<int:task_id>/file/", TaskFileDownloadAPIView.as_view()),
    path("<int:course_id>/cover/", CourseCoverUpload.as_view()),
    path("<int:course_id>/publish/", PublishCourse.as_view()),
    path("<int:course_id>/enroll/", CourseEnrollmentAPIView.as_view()),
]

urlpatterns += router.urls
