from celery import shared_task
from planning.models import Activite

@shared_task
def check_activity_alerts_task():
    Activite.check_activity_alerts()