from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Student views
    path('discover/', views.course_discover, name='discover'),
    path('<int:course_id>/join/', views.course_join, name='join'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/toggle/', views.toggle_task_completion, name='toggle_task'),

    # Teacher views
    path('manage/', views.teacher_dashboard, name='teacher_dashboard'),
    path('create/', views.course_create, name='create'),
    path('<int:course_id>/edit/', views.course_edit, name='edit'),
    path('<int:course_id>/detail/', views.course_detail, name='detail'),
    path('<int:course_id>/tasks/add/', views.task_add, name='task_add'),
]
