from django.contrib import admin
from apps.courses.models import Enrollment,Category, Course, Module, Task, Review, CompletedTask

# Register your models here.
admin.site.register(Enrollment)
admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Task)
admin.site.register(CompletedTask)
admin.site.register(Review)
