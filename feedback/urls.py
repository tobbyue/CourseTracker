from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('course/<int:course_id>/rate/', views.rate_course, name='rate_course'),
    path('course/<int:course_id>/reviews/', views.course_reviews, name='course_reviews'),
]
