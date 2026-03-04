from django.contrib import admin
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'score', 'created_at')
    list_filter = ('score', 'course')
    search_fields = ('student__username', 'course__title')
