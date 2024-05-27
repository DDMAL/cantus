from celery import Celery

app = Celery("cantusdata")
from . import settings

app.config_from_object(settings, namespace="CELERY")
app.autodiscover_tasks()
app.amqp.argsrepr_maxsize = 100000
app.amqp.kwargsrepr_maxsize = 100000
