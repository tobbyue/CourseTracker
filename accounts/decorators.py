"""
Custom role-based access decorators for CourseTracker.
Ensures students and teachers can only access their respective pages.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(role, redirect_url='home'):
    """
    Decorator factory that restricts view access to users with a specific role.
    Combines login_required check with role verification.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                role_display = dict(request.user.ROLE_CHOICES).get(role, role)
                messages.warning(
                    request,
                    f'Access denied. This page is only available to {role_display}s.'
                )
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def student_required(view_func):
    """Restrict view to authenticated students only."""
    return role_required('student', redirect_url='home')(view_func)


def teacher_required(view_func):
    """Restrict view to authenticated teachers only."""
    return role_required('teacher', redirect_url='home')(view_func)
