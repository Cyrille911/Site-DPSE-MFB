from django.contrib import admin
from .models import News, NewsComment

# Enregistrer chaque modèle dans l'admin
admin.site.register(News)
admin.site.register(NewsComment)