import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import User
from courses.models import Course, Task, Enrollment, TaskCompletion


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
        self.assertIn('dashboard', response.url)

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


class StudentDashboardViewTest(TestCase):
    """Tests for the student dashboard view with tasks, stats, and filters."""

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='dash_student', password='TestPass123!', role='student'
        )
        self.teacher = User.objects.create_user(
            username='dash_teacher', password='TestPass123!', role='teacher'
        )
        # Create course with tasks
        self.course = Course.objects.create(
            title='Test Course', course_code='TC101',
            description='A test course', teacher=self.teacher
        )
        self.task1 = Task.objects.create(
            course=self.course, title='Task 1',
            deadline=timezone.now() + timezone.timedelta(days=7)
        )
        self.task2 = Task.objects.create(
            course=self.course, title='Task 2',
            deadline=timezone.now() - timezone.timedelta(days=1)  # overdue
        )
        self.task3 = Task.objects.create(
            course=self.course, title='Task 3',
            deadline=timezone.now() + timezone.timedelta(days=2)  # due soon
        )
        # Enroll student
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_dashboard_loads_with_stats(self):
        """Dashboard shows correct stat cards."""
        self.client.login(username='dash_student', password='TestPass123!')
        response = self.client.get(reverse('courses:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['joined_count'], 1)
        self.assertEqual(response.context['total_tasks'], 3)
        self.assertEqual(response.context['completed_count'], 0)
        self.assertEqual(response.context['pending_count'], 3)

    def test_dashboard_shows_overdue_tasks(self):
        """Dashboard correctly identifies overdue tasks."""
        self.client.login(username='dash_student', password='TestPass123!')
        response = self.client.get(reverse('courses:student_dashboard'))
        self.assertEqual(response.context['overdue_count'], 1)

    def test_dashboard_progress_zero_when_nothing_done(self):
        """Progress percentage is 0 when no tasks completed."""
        self.client.login(username='dash_student', password='TestPass123!')
        response = self.client.get(reverse('courses:student_dashboard'))
        self.assertEqual(response.context['progress_pct'], 0)

    def test_dashboard_progress_updates_after_completion(self):
        """Progress percentage updates after completing a task."""
        TaskCompletion.objects.create(
            student=self.student, task=self.task1,
            is_completed=True, completed_at=timezone.now()
        )
        self.client.login(username='dash_student', password='TestPass123!')
        response = self.client.get(reverse('courses:student_dashboard'))
        self.assertEqual(response.context['completed_count'], 1)
        self.assertEqual(response.context['progress_pct'], 33)

    def test_dashboard_course_progress(self):
        """Per-course progress is included in context."""
        self.client.login(username='dash_student', password='TestPass123!')
        response = self.client.get(reverse('courses:student_dashboard'))
        self.assertEqual(len(response.context['course_progress']), 1)
        cp = response.context['course_progress'][0]
        self.assertEqual(cp['course'], self.course)
        self.assertEqual(cp['total_tasks'], 3)

    def test_dashboard_sort_by_course(self):
        """Sort by course query param works."""
        self.client.login(username='dash_student', password='TestPass123!')
        response = self.client.get(
            reverse('courses:student_dashboard') + '?sort=course'
        )
        self.assertEqual(response.status_code, 200)

    def test_dashboard_filter_by_status(self):
        """Filter by completed status query param works."""
        TaskCompletion.objects.create(
            student=self.student, task=self.task1,
            is_completed=True, completed_at=timezone.now()
        )
        self.client.login(username='dash_student', password='TestPass123!')
        response = self.client.get(
            reverse('courses:student_dashboard') + '?status=completed'
        )
        self.assertEqual(len(response.context['task_list']), 1)

    def test_dashboard_empty_when_not_enrolled(self):
        """Dashboard shows zero tasks when student has no enrollments."""
        new_student = User.objects.create_user(
            username='lonely_student', password='TestPass123!', role='student'
        )
        self.client.login(username='lonely_student', password='TestPass123!')
        response = self.client.get(reverse('courses:student_dashboard'))
        self.assertEqual(response.context['total_tasks'], 0)
        self.assertEqual(response.context['joined_count'], 0)

    def test_dashboard_contains_accessibility_landmarks(self):
        """Dashboard HTML includes aria-label sections for accessibility."""
        self.client.login(username='dash_student', password='TestPass123!')
        response = self.client.get(reverse('courses:student_dashboard'))
        content = response.content.decode()
        self.assertIn('aria-label="Progress overview"', content)
        self.assertIn('aria-label="Task list"', content)
        self.assertIn('aria-live="polite"', content)


class ToggleTaskCompletionTest(TestCase):
    """Tests for the AJAX task completion toggle endpoint."""

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='toggle_student', password='TestPass123!', role='student'
        )
        self.teacher = User.objects.create_user(
            username='toggle_teacher', password='TestPass123!', role='teacher'
        )
        self.course = Course.objects.create(
            title='Toggle Course', course_code='TG101',
            description='Test', teacher=self.teacher
        )
        self.task = Task.objects.create(
            course=self.course, title='Toggle Task',
            deadline=timezone.now() + timezone.timedelta(days=5)
        )
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_toggle_creates_completion(self):
        """First toggle creates a TaskCompletion set to True."""
        self.client.login(username='toggle_student', password='TestPass123!')
        response = self.client.post(
            reverse('courses:toggle_task', args=[self.task.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['is_completed'])
        self.assertEqual(data['stats']['completed'], 1)

    def test_toggle_twice_uncompletes(self):
        """Toggling twice reverts back to incomplete."""
        self.client.login(username='toggle_student', password='TestPass123!')
        url = reverse('courses:toggle_task', args=[self.task.id])
        self.client.post(url, content_type='application/json')
        response = self.client.post(url, content_type='application/json')
        data = json.loads(response.content)
        self.assertFalse(data['is_completed'])
        self.assertEqual(data['stats']['completed'], 0)

    def test_toggle_returns_updated_stats(self):
        """Toggle response includes correct progress stats."""
        self.client.login(username='toggle_student', password='TestPass123!')
        response = self.client.post(
            reverse('courses:toggle_task', args=[self.task.id]),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertIn('stats', data)
        self.assertEqual(data['stats']['total'], 1)
        self.assertEqual(data['stats']['progress_pct'], 100)

    def test_toggle_requires_post(self):
        """GET request to toggle should return 405."""
        self.client.login(username='toggle_student', password='TestPass123!')
        response = self.client.get(
            reverse('courses:toggle_task', args=[self.task.id])
        )
        self.assertEqual(response.status_code, 405)

    def test_toggle_requires_authentication(self):
        """Unauthenticated user should be redirected."""
        response = self.client.post(
            reverse('courses:toggle_task', args=[self.task.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class AccessibilityTest(TestCase):
    """Tests verifying WCAG accessibility features in templates."""

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='a11y_student', password='TestPass123!', role='student'
        )

    def test_login_has_skip_link(self):
        """Login page includes skip-to-main-content link (WCAG 2.1.1)."""
        response = self.client.get(reverse('accounts:login'))
        content = response.content.decode()
        self.assertIn('skip-link', content)
        self.assertIn('#main-content', content)

    def test_login_has_form_aria_label(self):
        """Login form has aria-label attribute."""
        response = self.client.get(reverse('accounts:login'))
        self.assertContains(response, 'aria-label="Login form"')

    def test_register_has_form_aria_label(self):
        """Register form has aria-label attribute."""
        response = self.client.get(reverse('accounts:register'))
        self.assertContains(response, 'aria-label="Registration form"')

    def test_main_content_landmark(self):
        """Pages include main landmark with id for skip link."""
        response = self.client.get(reverse('accounts:login'))
        self.assertContains(response, 'id="main-content"')
        self.assertContains(response, '<main')

    def test_nav_has_aria_label(self):
        """Navigation bar has aria-label for screen readers."""
        response = self.client.get(reverse('accounts:login'))
        self.assertContains(response, 'aria-label="Main navigation"')

    def test_profile_has_form_aria_label(self):
        """Profile edit form has aria-label."""
        self.client.login(username='a11y_student', password='TestPass123!')
        response = self.client.get(reverse('accounts:profile'))
        self.assertContains(response, 'aria-label="Edit profile form"')

    def test_password_change_has_form_aria_label(self):
        """Password change form has aria-label."""
        self.client.login(username='a11y_student', password='TestPass123!')
        response = self.client.get(reverse('accounts:password_change'))
        self.assertContains(response, 'aria-label="Change password form"')

    def test_messages_have_role_status(self):
        """Flash messages container has role=status for screen readers."""
        self.client.login(username='a11y_student', password='TestPass123!')
        # Login triggers a success message
        response = self.client.get(reverse('accounts:login'), follow=True)
        content = response.content.decode()
        # Check that base.html messages have aria-live
        self.assertIn('aria-live="polite"', content)
