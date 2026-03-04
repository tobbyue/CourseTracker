from django.contrib import admin
from .models import Course, Task, Enrollment, TaskCompletion


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_code', 'teacher', 'enrolled_count', 'created_at')
    search_fields = ('title', 'course_code')
    list_filter = ('created_at',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'deadline', 'created_at')
    list_filter = ('deadline', 'course')
    search_fields = ('title',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('course',)


@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ('student', 'task', 'is_completed', 'completed_at')
    list_filter = ('is_completed',)
