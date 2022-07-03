import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cantusdata.settings")
app = Celery("cantusdata")
import cantusdata.settings as settings
#app.config_from_object("django.conf:settings", namespace="CELERY")
app.config_from_object(settings, namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
