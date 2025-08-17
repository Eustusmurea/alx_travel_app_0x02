import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_travel_app.settings")

app = Celery("alx_travel_app")

# Load settings from Django, using CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks from all apps
app.autodiscover_tasks()