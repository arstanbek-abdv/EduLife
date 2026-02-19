from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.courses.course_views import (
    CourseCatalog, HomeAPIView,
    EnrollToCourseAPIView, UnenrollCourseAPIView,
    TaskFileDownloadAPIView, ProgressCountAPIView,
    StudentDashboard
)
from apps.courses.course_creation import (
    CreateCourseAPIView, CreateModuleAPIView,
    CreateTaskAPIView , TaskFileUpload,
    CourseCoverUpload, PublishCourse
)
from apps.courses.review_views import ReviewViewSet
from apps.courses.module_task_views import ModuleViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    path('all-courses/', HomeAPIView.as_view()),
    path('catalog/', CourseCatalog.as_view({'get': 'list'})),
    path('catalog/<int:pk>/', CourseCatalog.as_view({'get':'retrieve'})),
    path('my-courses/', StudentDashboard.as_view()),
    path('new-course/', CreateCourseAPIView.as_view()),
    path('new-course/<int:course_id>/modules/', CreateModuleAPIView.as_view()),
    path('modules/<int:module_id>/tasks/',CreateTaskAPIView.as_view()),
    path("tasks/<int:task_id>/upload/", TaskFileUpload.as_view()),
    path("tasks/<int:task_id>/file/", TaskFileDownloadAPIView.as_view()),
    path('tasks/<int:task_id>/progress/', ProgressCountAPIView.as_view()),
    path("<int:course_id>/cover/", CourseCoverUpload.as_view()),
    path("<int:course_id>/publish/", PublishCourse.as_view()),
    path("<int:course_id>/enroll/", EnrollToCourseAPIView.as_view()),
    path('<int:course_id>/unenroll/', UnenrollCourseAPIView.as_view()),
]
