from django import forms
from .models import Course, Task


class CourseForm(forms.ModelForm):
    """Form for teachers to create and edit courses."""

    class Meta:
        model = Course
        fields = ('title', 'course_code', 'description')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Course Name',
                'aria-label': 'Course Name',
            }),
            'course_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., BIO101',
                'aria-label': 'Course Code',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your course...',
                'rows': 4,
                'aria-label': 'Course Description',
            }),
        }


class TaskForm(forms.ModelForm):
    """Form for teachers to add tasks/assignments to a course."""

    class Meta:
        model = Task
        fields = ('title', 'description', 'deadline')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Task Title',
                'aria-label': 'Task Title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Task instructions (optional)',
                'rows': 3,
                'aria-label': 'Task Description',
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'aria-label': 'Deadline',
            }),
        }
