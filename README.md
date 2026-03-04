# CourseTracker - Course Management and Tracking System

**Group CT** | ITECH Web Application Implementation

A comprehensive educational platform designed to streamline the interaction between teachers and students in a digital learning environment.

## Features

- **User Authentication (M1)**: Registration and login with Student/Teacher role selection
- **Course Management (M2)**: Teachers can create, edit, and manage courses
- **Task Assignment (M3)**: Teachers add tasks with deadlines to courses
- **Course Discovery (M4, C1)**: Students browse and search courses by name or code
- **Task Tracking (M5, S2)**: Students mark tasks complete, sort/filter by deadline or status
- **Rating & Feedback (M6, S1)**: Students rate courses (1-5 stars) and leave comments

## Tech Stack

- **Backend**: Python 3 + Django 5
- **Frontend**: Django Templates + Bootstrap 5 + JavaScript (AJAX)
- **Database**: SQLite (development) / PostgreSQL (production)
- **CSS Framework**: Bootstrap 5.3

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd CourseTracker

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create a superuser (optional, for admin access)
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

## Project Structure

```
CourseTracker/
├── accounts/          # User auth (registration, login, logout)
├── courses/           # Course CRUD, task management, enrollment
├── feedback/          # Rating and review system
├── course_management/ # Django project settings
├── templates/         # HTML templates (base + per-app)
├── static/            # CSS, JavaScript, images
└── manage.py
```

## Running Tests

```bash
python manage.py test
```

## Team

| Member | Contribution |
|--------|-------------|
| Minghao Yue | Auth system, Student Dashboard, Deployment |
| Vugar Gurbanov | Course system, Task management, Design Spec |
| Xijie Luo | Rating system, Accessibility, CSS/Testing |

## License

This project is developed for academic purposes as part of the ITECH coursework.
