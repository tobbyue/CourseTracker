from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from courses.models import Course, Enrollment
from .models import Rating

User = get_user_model()


class RatingModelTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@example.com',
            password='testpass123',
            role='teacher'
        )

        self.student = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='testpass123',
            role='student'
        )

        self.course = Course.objects.create(
            title='Test Course',
            description='A course for testing ratings',
            course_code='TEST101',
            teacher=self.teacher
        )

    def test_rating_string_representation(self):
        rating = Rating.objects.create(
            student=self.student,
            course=self.course,
            score=4,
            comment='Good course'
        )
        self.assertIn(self.student.username, str(rating))
        self.assertIn(self.course.title, str(rating))

    def test_one_student_one_course_one_rating(self):
        Rating.objects.create(
            student=self.student,
            course=self.course,
            score=5,
            comment='Excellent'
        )

        with self.assertRaises(Exception):
            Rating.objects.create(
                student=self.student,
                course=self.course,
                score=3,
                comment='Trying to rate again'
            )

    def test_course_average_rating(self):
        student2 = User.objects.create_user(
            username='student2',
            email='student2@example.com',
            password='testpass123',
            role='student'
        )

        Rating.objects.create(
            student=self.student,
            course=self.course,
            score=4,
            comment='Nice'
        )
        Rating.objects.create(
            student=student2,
            course=self.course,
            score=2,
            comment='Not bad'
        )

        self.assertEqual(self.course.average_rating(), 3.0)


class RatingViewTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@example.com',
            password='testpass123',
            role='teacher'
        )

        self.student = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='testpass123',
            role='student'
        )

        self.other_student = User.objects.create_user(
            username='student2',
            email='student2@example.com',
            password='testpass123',
            role='student'
        )

        self.course = Course.objects.create(
            title='Web Dev Course',
            description='Learn web development',
            course_code='WEB101',
            teacher=self.teacher
        )

        Enrollment.objects.create(
            student=self.student,
            course=self.course
        )

    def test_enrolled_student_can_open_rate_page(self):
        self.client.login(username='student1', password='testpass123')
        url = reverse('feedback:rate_course', args=[self.course.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.title)

    def test_non_enrolled_student_cannot_rate_course(self):
        self.client.login(username='student2', password='testpass123')
        url = reverse('feedback:rate_course', args=[self.course.id])
        response = self.client.post(url, {
            'score': 5,
            'comment': 'Amazing!'
        }, follow=True)

        self.assertRedirects(response, reverse('courses:discover'))
        self.assertContains(response, 'You must be enrolled in a course to rate it.')
        self.assertEqual(Rating.objects.count(), 0)

    def test_enrolled_student_can_submit_rating(self):
        self.client.login(username='student1', password='testpass123')
        url = reverse('feedback:rate_course', args=[self.course.id])

        response = self.client.post(url, {
            'score': 4,
            'comment': 'Very useful course'
        }, follow=True)

        self.assertRedirects(response, reverse('courses:detail', kwargs={'course_id': self.course.id}))
        self.assertEqual(Rating.objects.count(), 1)

        rating = Rating.objects.first()
        self.assertEqual(rating.student, self.student)
        self.assertEqual(rating.course, self.course)
        self.assertEqual(rating.score, 4)
        self.assertEqual(rating.comment, 'Very useful course')

    def test_existing_rating_is_updated_not_duplicated(self):
        Rating.objects.create(
            student=self.student,
            course=self.course,
            score=3,
            comment='Initial rating'
        )

        self.client.login(username='student1', password='testpass123')
        url = reverse('feedback:rate_course', args=[self.course.id])

        response = self.client.post(url, {
            'score': 5,
            'comment': 'Updated rating'
        }, follow=True)

        self.assertRedirects(response, reverse('courses:detail', kwargs={'course_id': self.course.id}))
        self.assertEqual(Rating.objects.count(), 1)

        rating = Rating.objects.first()
        self.assertEqual(rating.score, 5)
        self.assertEqual(rating.comment, 'Updated rating')

    def test_course_reviews_page_loads(self):
        Rating.objects.create(
            student=self.student,
            course=self.course,
            score=4,
            comment='Helpful course'
        )

        self.client.login(username='student1', password='testpass123')
        url = reverse('feedback:course_reviews', args=[self.course.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.title)
        self.assertContains(response, 'Helpful course')
