from django.db import models
from django.conf import settings


class Course(models.Model):
    """
    Represents a course created by a teacher.
    Students can discover, join, and rate courses.
    """
    title = models.CharField(max_length=200, help_text='The name of the course.')
    description = models.TextField(blank=True, help_text='A brief description of the course.')
    course_code = models.CharField(
        max_length=20,
        unique=True,
        help_text='A unique identifier code for the course (e.g., BIO101).'
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='taught_courses',
        help_text='The teacher who created and owns this course.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.course_code})"

    def enrolled_count(self):
        """Returns the number of students enrolled in this course."""
        return self.enrollments.count()

    def average_rating(self):
        """Returns the average star rating for this course, or None if no ratings."""
        avg = self.ratings.aggregate(models.Avg('score'))['score__avg']
        return round(avg, 1) if avg else None


class Task(models.Model):
    """
    Represents an assignment/task within a course, created by the teacher.
    Has a title and deadline for students to track.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text='The course this task belongs to.'
    )
    title = models.CharField(max_length=200, help_text='The title of the task/assignment.')
    description = models.TextField(blank=True, help_text='Detailed instructions for the task.')
    deadline = models.DateTimeField(help_text='The deadline for completing this task.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['deadline']

    def __str__(self):
        return f"{self.course.course_code} - {self.title} (due: {self.deadline.strftime('%Y-%m-%d')})"


class Enrollment(models.Model):
    """
    Represents a student's enrollment in a course.
    Many-to-many relationship between User (student) and Course.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text='The student enrolled in the course.'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text='The course the student is enrolled in.'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course'],
                name='unique_enrollment'
            )
        ]
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"


class TaskCompletion(models.Model):
    """
    Tracks whether a student has completed a specific task.
    One record per student per task.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_completions',
        help_text='The student who completed the task.'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='completions',
        help_text='The task that was completed.'
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'task'],
                name='unique_task_completion'
            )
        ]
        ordering = ['-completed_at']
        verbose_name_plural = 'Tasks completions'

    def __str__(self):
        status = "Completed" if self.is_completed else "Pending"
        return f"{self.student.username} - {self.task.title}: {status}"
