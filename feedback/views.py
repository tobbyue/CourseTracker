from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from courses.models import Course, Enrollment
from .models import Rating
from .forms import RatingForm


@login_required
def rate_course(request, course_id):
    """Submit or update a rating for a course. [Implements M6]"""
    course = get_object_or_404(Course, id=course_id)

    is_enrolled = Enrollment.objects.filter(
        student=request.user, course=course
    ).exists()

    if not is_enrolled:
        messages.warning(request, 'You must be enrolled in a course to rate it.')
        return redirect('courses:discover')

    existing_rating = Rating.objects.filter(
        student=request.user, course=course
    ).first()

    if request.method == 'POST':
        form = RatingForm(request.POST, instance=existing_rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.student = request.user
            rating.course = course
            rating.save()
            action = 'updated' if existing_rating else 'submitted'
            messages.success(request, f'Your rating has been {action}!')
            return redirect('courses:detail', course_id=course.id)
    else:
        form = RatingForm(instance=existing_rating)

    context = {
        'form': form,
        'course': course,
        'existing_rating': existing_rating,
    }
    return render(request, 'feedback/rate_course.html', context)


@login_required
def course_reviews(request, course_id):
    """View all reviews/ratings for a course. [Implements S1]"""
    course = get_object_or_404(Course, id=course_id)
    ratings = Rating.objects.filter(course=course).select_related('student')

    context = {
        'course': course,
        'ratings': ratings,
        'avg_rating': course.average_rating(),
        'rating_count': ratings.count(),
    }
    return render(request, 'feedback/course_reviews.html', context)
