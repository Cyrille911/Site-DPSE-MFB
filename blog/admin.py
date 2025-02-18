from django.contrib import admin
from .models import Blog, BlogComment

# Enregistrer chaque modèle dans l'admin
admin.site.register(Blog)
admin.site.register(BlogComment)