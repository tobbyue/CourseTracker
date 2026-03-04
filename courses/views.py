from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from .models import Course, Task, Enrollment, TaskCompletion
from .forms import CourseForm, TaskForm


# ============================================================
# Student Views
# ============================================================

@login_required
def student_dashboard(request):
    """
    Student dashboard: shows enrolled courses, task progress,
    and task list with sort/filter capabilities.
    [Implements M5, S2]
    """
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    enrolled_courses = [e.course for e in enrollments]

    # Get all tasks from enrolled courses
    tasks = Task.objects.filter(course__in=enrolled_courses).select_related('course')

    # Get completion status for this student
    completions = TaskCompletion.objects.filter(
        student=request.user,
        task__in=tasks
    ).values_list('task_id', 'is_completed')
    completion_map = dict(completions)

    # Build task list with completion info
    task_list = []
    for task in tasks:
        task_list.append({
            'task': task,
            'is_completed': completion_map.get(task.id, False),
        })

    # Sort/filter from query parameters
    sort_by = request.GET.get('sort', 'deadline')
    filter_status = request.GET.get('status', 'all')

    if filter_status == 'completed':
        task_list = [t for t in task_list if t['is_completed']]
    elif filter_status == 'pending':
        task_list = [t for t in task_list if not t['is_completed']]

    if sort_by == 'deadline':
        task_list.sort(key=lambda t: t['task'].deadline)
    elif sort_by == 'course':
        task_list.sort(key=lambda t: t['task'].course.title)

    # Stats
    total_tasks = Task.objects.filter(course__in=enrolled_courses).count()
    completed_count = TaskCompletion.objects.filter(
        student=request.user,
        is_completed=True,
        task__course__in=enrolled_courses
    ).count()

    context = {
        'enrolled_courses': enrolled_courses,
        'task_list': task_list,
        'joined_count': len(enrolled_courses),
        'completed_count': completed_count,
        'total_tasks': total_tasks,
        'current_sort': sort_by,
        'current_filter': filter_status,
    }
    return render(request, 'courses/student_dashboard.html', context)


@login_required
def course_discover(request):
    """
    Course discovery page: browse and search all available courses.
    [Implements M4, C1]
    """
    query = request.GET.get('q', '').strip()
    courses = Course.objects.all().select_related('teacher')

    if query:
        courses = courses.filter(
            Q(title__icontains=query) | Q(course_code__icontains=query)
        )

    # Check which courses the student has already joined
    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(
            Enrollment.objects.filter(student=request.user)
            .values_list('course_id', flat=True)
        )

    # AJAX search support
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        course_data = []
        for course in courses:
            course_data.append({
                'id': course.id,
                'title': course.title,
                'course_code': course.course_code,
                'description': course.description[:100],
                'teacher': course.teacher.username,
                'avg_rating': course.average_rating(),
                'enrolled_count': course.enrolled_count(),
                'is_enrolled': course.id in enrolled_ids,
            })
        return JsonResponse({'courses': course_data})

    context = {
        'courses': courses,
        'enrolled_ids': enrolled_ids,
        'query': query,
    }
    return render(request, 'courses/discover.html', context)


@login_required
def course_join(request, course_id):
    """Join a course (student only). [Implements M4]"""
    course = get_object_or_404(Course, id=course_id)

    if request.user.is_teacher():
        messages.warning(request, 'Teachers cannot join courses.')
        return redirect('courses:discover')

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user, course=course
    )

    if created:
        messages.success(request, f'Successfully joined "{course.title}"!')
    else:
        messages.info(request, f'You are already enrolled in "{course.title}".')

    return redirect('courses:discover')


@login_required
def task_detail(request, task_id):
    """Task detail page. [Implements M5]"""
    task = get_object_or_404(Task, id=task_id)

    is_enrolled = Enrollment.objects.filter(
        student=request.user, course=task.course
    ).exists()

    completion = TaskCompletion.objects.filter(
        student=request.user, task=task
    ).first()

    context = {
        'task': task,
        'is_enrolled': is_enrolled,
        'is_completed': completion.is_completed if completion else False,
    }
    return render(request, 'courses/task_detail.html', context)


@login_required
def toggle_task_completion(request, task_id):
    """Toggle task completion status via AJAX. [Implements M5]"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    task = get_object_or_404(Task, id=task_id)

    completion, created = TaskCompletion.objects.get_or_create(
        student=request.user, task=task,
        defaults={'is_completed': True, 'completed_at': timezone.now()}
    )

    if not created:
        completion.is_completed = not completion.is_completed
        completion.completed_at = timezone.now() if completion.is_completed else None
        completion.save()

    return JsonResponse({
        'is_completed': completion.is_completed,
        'task_id': task.id,
    })


# ============================================================
# Teacher Views
# ============================================================

@login_required
def teacher_dashboard(request):
    """Teacher dashboard: overview of owned courses. [Implements M2]"""
    if not request.user.is_teacher():
        messages.warning(request, 'Only teachers can access this page.')
        return redirect('courses:student_dashboard')

    courses = Course.objects.filter(teacher=request.user).annotate(
        student_count=Count('enrollments'),
        task_count=Count('tasks'),
    )
    return render(request, 'courses/teacher_dashboard.html', {'courses': courses})


@login_required
def course_create(request):
    """Create a new course (teacher only). [Implements M2]"""
    if not request.user.is_teacher():
        messages.warning(request, 'Only teachers can create courses.')
        return redirect('home')

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, f'Course "{course.title}" created successfully!')
            return redirect('courses:detail', course_id=course.id)
    else:
        form = CourseForm()

    return render(request, 'courses/course_form.html', {'form': form, 'action': 'Create'})


@login_required
def course_edit(request, course_id):
    """Edit an existing course (owner only). [Implements M2]"""
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course "{course.title}" updated successfully!')
            return redirect('courses:detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)

    return render(request, 'courses/course_form.html', {'form': form, 'action': 'Edit', 'course': course})


@login_required
def course_detail(request, course_id):
    """
    Course detail page: shows info, enrolled students, tasks, and completion stats.
    [Addressing sitemap feedback - teacher course info display/edit page]
    """
    course = get_object_or_404(Course, id=course_id)
    is_owner = course.teacher == request.user
    tasks = course.tasks.all()
    enrollments = course.enrollments.select_related('student').all()

    task_stats = []
    for task in tasks:
        completed = task.completions.filter(is_completed=True).count()
        task_stats.append({
            'task': task,
            'completed': completed,
            'total': enrollments.count(),
        })

    context = {
        'course': course,
        'is_owner': is_owner,
        'tasks': tasks,
        'task_stats': task_stats,
        'enrollments': enrollments,
        'avg_rating': course.average_rating(),
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def task_add(request, course_id):
    """Add a task to a course (owner teacher only). [Implements M3]"""
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.course = course
            task.save()
            messages.success(request, f'Task "{task.title}" added successfully!')
            return redirect('courses:detail', course_id=course.id)
    else:
        form = TaskForm()

    return render(request, 'courses/task_form.html', {'form': form, 'course': course})
