from django.contrib import admin
from .models import PlanAction, Effet, Produit, Action, Activite

# Enregistrer chaque modèle dans l'admin
admin.site.register(PlanAction)
admin.site.register(Effet)
admin.site.register(Produit)
admin.site.register(Action)
admin.site.register(Activite)