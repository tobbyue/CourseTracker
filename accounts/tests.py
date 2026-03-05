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

    def test_default_role_is_student(self):
        """Test that the default role is student."""
        user = User.objects.create_user(username='default_user', password='testpass123')
        self.assertEqual(user.role, 'student')
        self.assertTrue(user.is_student())


class AuthViewTest(TestCase):
    """Tests for authentication views."""

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='teststudent', password='TestPass123!', role='student',
            email='student@example.com'
        )
        self.teacher = User.objects.create_user(
            username='testteacher', password='TestPass123!', role='teacher',
            email='teacher@example.com'
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In')

    def test_register_page_loads(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')

    def test_login_valid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'teststudent',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'teststudent',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page

    def test_register_new_student(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newstudent',
            'email': 'new@example.com',
            'role': 'student',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after register
        user = User.objects.get(username='newstudent')
        self.assertEqual(user.role, 'student')
        self.assertEqual(user.email, 'new@example.com')

    def test_register_new_teacher(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newteacher',
            'email': 'newteacher@example.com',
            'role': 'teacher',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newteacher')
        self.assertEqual(user.role, 'teacher')

    def test_register_duplicate_email(self):
        """Test that registering with an existing email fails."""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'anotheruser',
            'email': 'student@example.com',  # Already taken
            'role': 'student',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 200)  # Stays on page with errors
        self.assertFalse(User.objects.filter(username='anotheruser').exists())

    def test_register_password_mismatch(self):
        """Test that mismatched passwords fail registration."""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'role': 'student',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())

    def test_logout_redirects_to_login(self):
        """Test that logout redirects to the login page."""
        self.client.login(username='teststudent', password='TestPass123!')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_authenticated_user_redirected_from_login(self):
        """Test that already-logged-in users are redirected away from login."""
        self.client.login(username='teststudent', password='TestPass123!')
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_redirected_from_register(self):
        """Test that already-logged-in users are redirected away from register."""
        self.client.login(username='teststudent', password='TestPass123!')
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 302)


class HomeRedirectTest(TestCase):
    """Test that the home view correctly redirects based on user role."""

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='student_home', password='TestPass123!', role='student'
        )
        self.teacher = User.objects.create_user(
            username='teacher_home', password='TestPass123!', role='teacher'
        )

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_student_redirects_to_student_dashboard(self):
        self.client.login(username='student_home', password='TestPass123!')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('student', response.url)

    def test_teacher_redirects_to_teacher_dashboard(self):
        self.client.login(username='teacher_home', password='TestPass123!')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('manage', response.url)


class ProfileViewTest(TestCase):
    """Tests for the user profile and password change views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='profileuser', password='TestPass123!',
            role='student', email='profile@example.com',
            first_name='Test', last_name='User'
        )

    def test_profile_page_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_profile_page_loads(self):
        self.client.login(username='profileuser', password='TestPass123!')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Profile')
        self.assertContains(response, 'profileuser')

    def test_update_profile(self):
        self.client.login(username='profileuser', password='TestPass123!')
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_update_profile_duplicate_email(self):
        """Test that updating to an existing email fails."""
        User.objects.create_user(
            username='otheruser', password='TestPass123!',
            email='taken@example.com'
        )
        self.client.login(username='profileuser', password='TestPass123!')
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'taken@example.com',
        })
        self.assertEqual(response.status_code, 200)  # Stays on page
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'profile@example.com')  # Unchanged

    def test_password_change_page_loads(self):
        self.client.login(username='profileuser', password='TestPass123!')
        response = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change Password')

    def test_password_change_success(self):
        self.client.login(username='profileuser', password='TestPass123!')
        response = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'TestPass123!',
            'new_password1': 'NewSecure456!',
            'new_password2': 'NewSecure456!',
        })
        self.assertEqual(response.status_code, 302)
        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecure456!'))

    def test_password_change_wrong_old_password(self):
        self.client.login(username='profileuser', password='TestPass123!')
        response = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'WrongOldPassword!',
            'new_password1': 'NewSecure456!',
            'new_password2': 'NewSecure456!',
        })
        self.assertEqual(response.status_code, 200)  # Stays on page
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('TestPass123!'))  # Unchanged


class RoleBasedAccessTest(TestCase):
    """Tests for role-based access control via decorators."""

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='access_student', password='TestPass123!', role='student'
        )
        self.teacher = User.objects.create_user(
            username='access_teacher', password='TestPass123!', role='teacher'
        )

    def test_student_cannot_access_teacher_dashboard(self):
        self.client.login(username='access_student', password='TestPass123!')
        response = self.client.get(reverse('courses:teacher_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirected away

    def test_teacher_cannot_access_student_dashboard(self):
        self.client.login(username='access_teacher', password='TestPass123!')
        response = self.client.get(reverse('courses:student_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirected away

    def test_student_can_access_student_dashboard(self):
        self.client.login(username='access_student', password='TestPass123!')
        response = self.client.get(reverse('courses:student_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_can_access_teacher_dashboard(self):
        self.client.login(username='access_teacher', password='TestPass123!')
        response = self.client.get(reverse('courses:teacher_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_can_access_course_create(self):
        self.client.login(username='access_teacher', password='TestPass123!')
        response = self.client.get(reverse('courses:create'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_course_create(self):
        self.client.login(username='access_student', password='TestPass123!')
        response = self.client.get(reverse('courses:create'))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(reverse('courses:student_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class RememberMeTest(TestCase):
    """Test the remember me functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='remember_user', password='TestPass123!', role='student'
        )

    def test_login_without_remember_me(self):
        """Session should expire on browser close when remember_me is off."""
        self.client.post(reverse('accounts:login'), {
            'username': 'remember_user',
            'password': 'TestPass123!',
        })
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_with_remember_me(self):
        """Session should persist when remember_me is on."""
        self.client.post(reverse('accounts:login'), {
            'username': 'remember_user',
            'password': 'TestPass123!',
            'remember_me': True,
        })
        self.assertFalse(self.client.session.get_expire_at_browser_close())
