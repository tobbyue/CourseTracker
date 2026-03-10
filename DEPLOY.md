# CourseTracker - Deployment Guide

## Render (Recommended)

### Quick Deploy
1. Push code to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo (CourseTracker)
4. Render auto-detects `render.yaml` — click **Apply**
5. Wait for build + deploy (takes ~3-5 min)
6. Your app will be at: `https://coursetracker-xxxx.onrender.com`

### Manual Config (if render.yaml not detected)
- **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- **Start Command**: `gunicorn course_management.wsgi`
- **Environment Variables**:
  - `DJANGO_SECRET_KEY` = (auto-generate)
  - `DJANGO_DEBUG` = `False`
  - `DJANGO_ALLOWED_HOSTS` = `.onrender.com`
  - `PYTHON_VERSION` = `3.11.6`

## PythonAnywhere (Alternative)

1. Upload code or `git clone` in PythonAnywhere Bash console
2. Create virtual env: `mkvirtualenv coursetracker --python=python3.11`
3. Install: `pip install -r requirements.txt`
4. Set env vars in `.env` or WSGI config:
   - `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=yourusername.pythonanywhere.com`
5. Go to Web tab → Add new web app → Manual config → Python 3.11
6. Set WSGI file to point to `course_management.wsgi`
7. Set static files: URL `/static/` → Directory `/home/yourusername/CourseTracker/staticfiles/`
8. Run: `python manage.py collectstatic --noinput && python manage.py migrate`
9. Reload web app

## Create Superuser (on deployed server)
```bash
python manage.py createsuperuser
```

## Environment Variables Reference
| Variable | Default | Production |
|---|---|---|
| DJANGO_SECRET_KEY | dev-key | Auto-generated |
| DJANGO_DEBUG | True | False |
| DJANGO_ALLOWED_HOSTS | localhost,127.0.0.1 | your-domain.com |
