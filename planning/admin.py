import json
from django.contrib import admin
from .models import PlanAction, Effet, Produit, Action, Activite, ActiviteLog

# Enregistrer chaque modèle dans l'admin
admin.site.register(PlanAction)
admin.site.register(Effet)
admin.site.register(Produit)
admin.site.register(Action)
@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display = ('reference', 'titre', 'type', 'structure', 'point_focal', 'responsable', 'created_at')
    list_filter = ('type', 'structure', 'created_at', 'point_focal', 'responsable')
    search_fields = ('titre', 'reference', 'structure')
    readonly_fields = ('reference',)

@admin.register(ActiviteLog)
class ActiviteLogAdmin(admin.ModelAdmin):
    list_display = ('activite', 'user', 'statut_apres', 'timestamp')
    list_filter = ('statut_apres', 'timestamp', 'user')
    search_fields = ('activite__titre', 'user__username')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

    def modifications_display(self, obj):
        return json.dumps(obj.modifications, indent=2, ensure_ascii=False)
    modifications_display.short_description = "Modifications"