from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from courses.models import Course, Enrollment
from .models import Rating
from .forms import RatingForm


class RatingModelTest(TestCase):
    """Tests for the Rating model."""

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

    def test_rating_creation(self):
        """A rating can be created with valid data."""
        rating = Rating.objects.create(
            student=self.student, course=self.course, score=4, comment='Great course!'
        )
        self.assertEqual(rating.score, 4)
        self.assertEqual(rating.comment, 'Great course!')
        self.assertEqual(rating.student, self.student)
        self.assertEqual(rating.course, self.course)

    def test_rating_str_representation(self):
        """String representation shows username, course title, and score."""
        rating = Rating.objects.create(
            student=self.student, course=self.course, score=5
        )
        self.assertEqual(str(rating), 'student1 rated Biology 101: 5/5')

    def test_rating_unique_constraint(self):
        """A student can only rate a course once."""
        Rating.objects.create(student=self.student, course=self.course, score=3)
        with self.assertRaises(Exception):
            Rating.objects.create(student=self.student, course=self.course, score=5)

    def test_rating_comment_optional(self):
        """Comment field can be left blank."""
        rating = Rating.objects.create(
            student=self.student, course=self.course, score=4
        )
        self.assertEqual(rating.comment, '')

    def test_rating_ordering(self):
        """Ratings are ordered by most recent first."""
        student2 = User.objects.create_user(
            username='student2', password='testpass123', role='student'
        )
        rating1 = Rating.objects.create(
            student=self.student, course=self.course, score=3
        )
        rating2 = Rating.objects.create(
            student=student2, course=self.course, score=5
        )
        ratings = list(Rating.objects.filter(course=self.course))
        self.assertEqual(ratings[0], rating2)
        self.assertEqual(ratings[1], rating1)

    def test_course_average_rating(self):
        """Course.average_rating() correctly calculates the average score."""
        student2 = User.objects.create_user(
            username='student2', password='testpass123', role='student'
        )
        Rating.objects.create(student=self.student, course=self.course, score=4)
        Rating.objects.create(student=student2, course=self.course, score=2)
        self.assertEqual(self.course.average_rating(), 3.0)

    def test_course_average_rating_none_when_no_ratings(self):
        """Course.average_rating() returns None when there are no ratings."""
        self.assertIsNone(self.course.average_rating())

    def test_rating_cascade_delete_student(self):
        """Deleting a student also deletes their ratings."""
        Rating.objects.create(student=self.student, course=self.course, score=4)
        self.assertEqual(Rating.objects.count(), 1)
        self.student.delete()
        self.assertEqual(Rating.objects.count(), 0)

    def test_rating_cascade_delete_course(self):
        """Deleting a course also deletes its ratings."""
        Rating.objects.create(student=self.student, course=self.course, score=4)
        self.assertEqual(Rating.objects.count(), 1)
        self.course.delete()
        self.assertEqual(Rating.objects.count(), 0)


class RatingFormTest(TestCase):
    """Tests for the RatingForm."""

    def test_valid_form(self):
        """Form is valid with a score between 1-5."""
        form = RatingForm(data={'score': 4, 'comment': 'Nice course'})
        self.assertTrue(form.is_valid())

    def test_valid_form_without_comment(self):
        """Form is valid without a comment."""
        form = RatingForm(data={'score': 3, 'comment': ''})
        self.assertTrue(form.is_valid())

    def test_invalid_form_no_score(self):
        """Form is invalid without a score."""
        form = RatingForm(data={'comment': 'No score given'})
        self.assertFalse(form.is_valid())
        self.assertIn('score', form.errors)

    def test_invalid_form_score_zero(self):
        """Form is invalid with score of 0."""
        form = RatingForm(data={'score': 0, 'comment': ''})
        self.assertFalse(form.is_valid())

    def test_invalid_form_score_six(self):
        """Form is invalid with score above 5."""
        form = RatingForm(data={'score': 6, 'comment': ''})
        self.assertFalse(form.is_valid())

    def test_form_fields(self):
        """Form only includes score and comment fields."""
        form = RatingForm()
        self.assertEqual(list(form.fields.keys()), ['score', 'comment'])


class RateCourseViewTest(TestCase):
    """Tests for the rate_course view."""

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
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_rate_course_requires_login(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('feedback:rate_course', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_rate_course_get(self):
        """Enrolled student can access the rating form."""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(
            reverse('feedback:rate_course', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feedback/rate_course.html')

    def test_rate_course_not_enrolled(self):
        """Non-enrolled student is redirected to discover page."""
        student2 = User.objects.create_user(
            username='student2', password='testpass123', role='student'
        )
        self.client.login(username='student2', password='testpass123')
        response = self.client.get(
            reverse('feedback:rate_course', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('courses:discover'))

    def test_submit_rating(self):
        """Enrolled student can submit a new rating."""
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('feedback:rate_course', args=[self.course.id]),
            {'score': 5, 'comment': 'Excellent course!'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Rating.objects.filter(
            student=self.student, course=self.course, score=5
        ).exists())

    def test_update_existing_rating(self):
        """Student can update their existing rating."""
        Rating.objects.create(
            student=self.student, course=self.course, score=3, comment='OK'
        )
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('feedback:rate_course', args=[self.course.id]),
            {'score': 5, 'comment': 'Actually great!'},
        )
        self.assertEqual(response.status_code, 302)
        rating = Rating.objects.get(student=self.student, course=self.course)
        self.assertEqual(rating.score, 5)
        self.assertEqual(rating.comment, 'Actually great!')

    def test_submit_invalid_rating(self):
        """Submitting invalid data re-renders the form."""
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('feedback:rate_course', args=[self.course.id]),
            {'score': '', 'comment': 'No score'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Rating.objects.filter(
            student=self.student, course=self.course
        ).exists())

    def test_rate_nonexistent_course(self):
        """Rating a non-existent course returns 404."""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(
            reverse('feedback:rate_course', args=[9999])
        )
        self.assertEqual(response.status_code, 404)


class CourseReviewsViewTest(TestCase):
    """Tests for the course_reviews view."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='teacher1', password='testpass123', role='teacher'
        )
        self.student = User.objects.create_user(
            username='student1', password='testpass123', role='student'
        )
        self.course = Course.objects.create(
            title='Physics 101', course_code='PHY101', teacher=self.teacher
        )

    def test_reviews_requires_login(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('feedback:course_reviews', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_reviews_page_loads(self):
        """Reviews page loads successfully for logged-in users."""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(
            reverse('feedback:course_reviews', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feedback/course_reviews.html')

    def test_reviews_shows_ratings(self):
        """Reviews page displays submitted ratings."""
        Enrollment.objects.create(student=self.student, course=self.course)
        Rating.objects.create(
            student=self.student, course=self.course,
            score=4, comment='Very informative'
        )
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(
            reverse('feedback:course_reviews', args=[self.course.id])
        )
        self.assertContains(response, 'Very informative')

    def test_reviews_context_data(self):
        """Reviews page contains correct context data."""
        Enrollment.objects.create(student=self.student, course=self.course)
        Rating.objects.create(
            student=self.student, course=self.course, score=4
        )
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(
            reverse('feedback:course_reviews', args=[self.course.id])
        )
        self.assertEqual(response.context['course'], self.course)
        self.assertEqual(response.context['rating_count'], 1)
        self.assertEqual(response.context['avg_rating'], 4.0)

    def test_reviews_nonexistent_course(self):
        """Viewing reviews for a non-existent course returns 404."""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(
            reverse('feedback:course_reviews', args=[9999])
        )
        self.assertEqual(response.status_code, 404)
