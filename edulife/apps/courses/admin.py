from django.contrib import admin
from apps.courses.models import Enrollment,Category, Course, Module, Lesson, Task, Submission

# Register your models here.
admin.site.register(Enrollment)
admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Task)
admin.site.register(Submission)