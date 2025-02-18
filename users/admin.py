from django.contrib import admin
from .models import User

# Enregistrer chaque modèle dans l'admin
admin.site.register(User)