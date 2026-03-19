from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from .models import Course, Task, Enrollment, TaskCompletion


class CourseModelTest(TestCase):
    """Tests for Course and related models."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher1', password='testpass123', role='teacher'
        )
        self.student = User.objects.create_user(
            username='student1', password='testpass123', role='student'
        )
        self.course = Course.objects.create(
            title='Biology 101',
            course_code='BIO101',
            description='Intro to Biology',
            teacher=self.teacher,
        )

    def test_course_creation(self):
        self.assertEqual(self.course.title, 'Biology 101')
        self.assertEqual(self.course.teacher, self.teacher)

    def test_course_code_unique(self):
        """Course code must be unique."""
        with self.assertRaises(Exception):
            Course.objects.create(
                title='Another Bio', course_code='BIO101', teacher=self.teacher
            )

    def test_enrolled_count(self):
        self.assertEqual(self.course.enrolled_count(), 0)
        Enrollment.objects.create(student=self.student, course=self.course)
        self.assertEqual(self.course.enrolled_count(), 1)

    def test_enrollment_unique_constraint(self):
        """A student can only enroll in a course once."""
        Enrollment.objects.create(student=self.student, course=self.course)
        with self.assertRaises(Exception):
            Enrollment.objects.create(student=self.student, course=self.course)
    
    def test_enrolled_count_multiple_students(self):
        student2 = User.objects.create_user(
            username='student2', password='testpass123', role='student'
        )
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=student2, course=self.course)
        self.assertEqual(self.course.enrolled_count(), 2)


class TaskModelTest(TestCase):
    """Tests for Task and TaskCompletion models."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher1', password='testpass123', role='teacher'
        )
        self.student = User.objects.create_user(
            username='student1', password='testpass123', role='student'
        )
        self.course = Course.objects.create(
            title='CS101', course_code='CS101', teacher=self.teacher
        )
        self.task = Task.objects.create(
            course=self.course,
            title='Assignment 1',
            deadline=timezone.now() + timedelta(days=7),
        )

    def test_task_creation(self):
        self.assertEqual(self.task.title, 'Assignment 1')
        self.assertEqual(self.task.course, self.course)

    def test_task_completion_toggle(self):
        completion = TaskCompletion.objects.create(
            student=self.student, task=self.task, is_completed=False
        )
        self.assertFalse(completion.is_completed)
        completion.is_completed = True
        completion.completed_at = timezone.now()
        completion.save()
        self.assertTrue(completion.is_completed)

    def test_task_completion_unique_constraint(self):
        """One completion record per student per task."""
        TaskCompletion.objects.create(student=self.student, task=self.task)
        with self.assertRaises(Exception):
            TaskCompletion.objects.create(student=self.student, task=self.task)

    def test_task_string_representation(self):
        self.assertIn('Assignment 1', str(self.task))

class CourseViewTest(TestCase):
    """Tests for course-related views."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='teacher1', password='testpass123', role='teacher'
        )
        self.student = User.objects.create_user(
            username='student1', password='testpass123', role='student'
        )
        self.course = Course.objects.create(
            title='Math 101', course_code='MATH101', teacher=self.teacher
        )

    def test_discover_page_requires_login(self):
        response = self.client.get(reverse('courses:discover'))
        self.assertEqual(response.status_code, 302)

    def test_discover_page_logged_in(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('courses:discover'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_dashboard_access(self):
        self.client.login(username='teacher1', password='testpass123')
        response = self.client.get(reverse('courses:teacher_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_teacher_dashboard(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('courses:teacher_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirected

    def test_course_create_by_teacher(self):
        self.client.login(username='teacher1', password='testpass123')
        response = self.client.post(reverse('courses:create'), {
            'title': 'New Course',
            'course_code': 'NEW101',
            'description': 'A new course',
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(Course.objects.filter(course_code='NEW101').exists())

    def test_join_course(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('courses:join', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Enrollment.objects.filter(
            student=self.student, course=self.course
        ).exists())
