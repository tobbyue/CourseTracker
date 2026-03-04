from django.test import TestCase, Client
from django.urls import reverse
from .models import User


class UserModelTest(TestCase):
    """Tests for the custom User model."""

    def setUp(self):
        self.student = User.objects.create_user(
            username='student1', password='testpass123', role='student'
        )
        self.teacher = User.objects.create_user(
            username='teacher1', password='testpass123', role='teacher'
        )

    def test_user_creation(self):
        """Test that users are created with correct role."""
        self.assertEqual(self.student.role, 'student')
        self.assertEqual(self.teacher.role, 'teacher')

    def test_is_student(self):
        self.assertTrue(self.student.is_student())
        self.assertFalse(self.student.is_teacher())

    def test_is_teacher(self):
        self.assertTrue(self.teacher.is_teacher())
        self.assertFalse(self.teacher.is_student())

    def test_str_representation(self):
        self.assertIn('student1', str(self.student))
        self.assertIn('Student', str(self.student))


class AuthViewTest(TestCase):
    """Tests for authentication views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123', role='student'
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page_loads(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_login_valid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page

    def test_register_new_user(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'role': 'student',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after register
        self.assertTrue(User.objects.filter(username='newuser').exists())
