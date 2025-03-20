import os
from celery import Celery

# Définir le module de settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votre_projet.settings')

# Créer une instance Celery
app = Celery('votre_projet')

# Charger la configuration depuis les settings Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans les applications Django
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')