import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cantusdata.settings")
app = Celery("cantusdata")
import cantusdata.settings as settings

app.config_from_object(settings, namespace="CELERY")
app.autodiscover_tasks()
app.amqp.argsrepr_maxsize = 100000
app.amqp.kwargsrepr_maxsize = 100000
