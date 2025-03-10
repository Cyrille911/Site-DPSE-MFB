from django.contrib import admin
from .models import Document_mfb, Document_dpse_planification, Document_dpse_suivi_evaluation, Document_dpse_statistiques, Document_dpse_qualite, Document_dpse_archives

# Enregistrer chaque modèle dans l'admin
admin.site.register(Document_mfb)
admin.site.register(Document_dpse_planification)
admin.site.register(Document_dpse_suivi_evaluation)
admin.site.register(Document_dpse_statistiques)
admin.site.register(Document_dpse_qualite)
admin.site.register(Document_dpse_archives)