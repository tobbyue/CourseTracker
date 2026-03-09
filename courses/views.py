from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from accounts.decorators import student_required, teacher_required
from .models import Course, Task, Enrollment, TaskCompletion
from .forms import CourseForm, TaskForm


# ============================================================
# Student Views
# ============================================================

@student_required
def student_dashboard(request):
    """
    Student dashboard: shows enrolled courses, task progress,
    and task list with sort/filter capabilities.
    [Implements M5, S2]
    """
    now = timezone.now()
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

    # Build task list with completion info and deadline status
    task_list = []
    for task in tasks:
        is_completed = completion_map.get(task.id, False)
        is_overdue = not is_completed and task.deadline < now
        is_due_soon = (not is_completed and not is_overdue
                       and task.deadline <= now + timezone.timedelta(days=3))
        task_list.append({
            'task': task,
            'is_completed': is_completed,
            'is_overdue': is_overdue,
            'is_due_soon': is_due_soon,
            'course_code': task.course.course_code,
        })

    # Sort/filter from query parameters (server-side fallback)
    sort_by = request.GET.get('sort', 'deadline')
    filter_status = request.GET.get('status', 'all')
    filter_course = request.GET.get('course', 'all')

    if filter_status == 'completed':
        task_list = [t for t in task_list if t['is_completed']]
    elif filter_status == 'pending':
        task_list = [t for t in task_list if not t['is_completed']]

    if filter_course and filter_course != 'all':
        task_list = [t for t in task_list if t['course_code'] == filter_course]

    if sort_by == 'deadline':
        task_list.sort(key=lambda t: t['task'].deadline)
    elif sort_by == 'course':
        task_list.sort(key=lambda t: t['task'].course.title)
    elif sort_by == 'status':
        task_list.sort(key=lambda t: (t['is_completed'], t['task'].deadline))

    # Stats
    total_tasks = Task.objects.filter(course__in=enrolled_courses).count()
    completed_count = TaskCompletion.objects.filter(
        student=request.user,
        is_completed=True,
        task__course__in=enrolled_courses
    ).count()
    pending_count = total_tasks - completed_count
    overdue_count = sum(1 for t in task_list if t.get('is_overdue', False))
    progress_pct = round(completed_count / total_tasks * 100) if total_tasks > 0 else 0

    # Per-course progress for enrolled courses section
    course_progress = []
    for course in enrolled_courses:
        course_tasks = Task.objects.filter(course=course).count()
        course_done = TaskCompletion.objects.filter(
            student=request.user, is_completed=True, task__course=course
        ).count()
        pct = round(course_done / course_tasks * 100) if course_tasks > 0 else 0
        course_progress.append({
            'course': course,
            'total_tasks': course_tasks,
            'completed_tasks': course_done,
            'progress_pct': pct,
        })

    # Unique course codes for filter dropdown
    course_codes = sorted(set(t.course.course_code for t in tasks))

    context = {
        'enrolled_courses': enrolled_courses,
        'task_list': task_list,
        'joined_count': len(enrolled_courses),
        'completed_count': completed_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'total_tasks': total_tasks,
        'progress_pct': progress_pct,
        'course_progress': course_progress,
        'course_codes': course_codes,
        'current_sort': sort_by,
        'current_filter': filter_status,
        'current_course': filter_course,
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

    # Return updated stats for live dashboard update
    enrolled_courses = list(
        Enrollment.objects.filter(student=request.user)
        .values_list('course_id', flat=True)
    )
    total = Task.objects.filter(course_id__in=enrolled_courses).count()
    done = TaskCompletion.objects.filter(
        student=request.user, is_completed=True,
        task__course_id__in=enrolled_courses
    ).count()

    return JsonResponse({
        'is_completed': completion.is_completed,
        'task_id': task.id,
        'stats': {
            'completed': done,
            'pending': total - done,
            'total': total,
            'progress_pct': round(done / total * 100) if total > 0 else 0,
        }
    })


# ============================================================
# Teacher Views
# ============================================================

@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard: overview of owned courses. [Implements M2]"""
    courses = Course.objects.filter(teacher=request.user).annotate(
        student_count=Count('enrollments'),
        task_count=Count('tasks'),
    )
    return render(request, 'courses/teacher_dashboard.html', {'courses': courses})


@teacher_required
def course_create(request):
    """Create a new course (teacher only). [Implements M2]"""
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


@teacher_required
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


@teacher_required
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
