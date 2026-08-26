from django.contrib import admin
from .models import Discussion

# Enregistrer chaque modèle dans l'admin
admin.site.register(Discussion)
