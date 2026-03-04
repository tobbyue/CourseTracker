from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Rating(models.Model):
    """
    Represents a student's rating and comment for a course.
    Each student can only rate a course once (enforced by unique constraint).
    Score is 1-5 stars.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings',
        help_text='The student who wrote this rating.'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='ratings',
        help_text='The course being rated.'
    )
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Star rating from 1 to 5.'
    )
    comment = models.TextField(
        blank=True,
        help_text='Optional text comment about the course.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course'],
                name='unique_rating_per_student_course'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} rated {self.course.title}: {self.score}/5"
