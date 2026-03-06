from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.courses.course_views import (
    CourseCatalog, HomeAPIView,
    EnrollToCourseAPIView, UnenrollCourseAPIView,
    TaskFileDownloadAPIView, CompleteTaskAPIView,
    CategoriesListAPIView,
)
from apps.courses.course_creation import (
    CreateEditCourse, CreateEditModule,
    CreateEditTask , TaskFileUpload,
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
    path('categories/', CategoriesListAPIView.as_view()),
    path('my-courses/', HomeAPIView.as_view()),
    path('catalog/', CourseCatalog.as_view({'get':'list'})),
    path('catalog/<int:course_id>/', CourseCatalog.as_view({'get':'retrieve'})),
    path('new-course/', CreateEditCourse.as_view({'post':'create'})),
    path('new-course/<int:pk>/', CreateEditCourse.as_view({'patch':'partial_update','delete':'destroy'})),
    path('new-course/<int:course_id>/modules/', CreateEditModule.as_view({'post':'create'})),
    path('new-course/<int:course_id>/modules/<int:pk>/', CreateEditModule.as_view({'patch':'partial_update','delete':'destroy'})),
    path('modules/<int:module_id>/tasks/', CreateEditTask.as_view({'post':'create'})),
    path('modules/<int:module_id>/tasks/<int:pk>/', CreateEditTask.as_view({'patch':'partial_update','delete':'destroy'})),
    path("tasks/<int:task_id>/upload/", TaskFileUpload.as_view()),
    path("tasks/<int:task_id>/file/", TaskFileDownloadAPIView.as_view()),
    path('tasks/<int:task_id>/complete/', CompleteTaskAPIView.as_view()),
    path("<int:course_id>/cover/", CourseCoverUpload.as_view()),
    path("<int:course_id>/publish/", PublishCourse.as_view()),
    path("<int:course_id>/enroll/", EnrollToCourseAPIView.as_view()),
    path('<int:course_id>/unenroll/', UnenrollCourseAPIView.as_view()),
]
