import json
from django.contrib import admin
from .models import PlanAction, Axe, Effet, IndicateurEffet, Produit, IndicateurProduit, Action, Activite, ActiviteLog, PreuveRealisation

# Enregistrer chaque modèle dans l'admin
admin.site.register(PlanAction)
admin.site.register(Axe)
admin.site.register(Effet)
admin.site.register(IndicateurEffet)
admin.site.register(Produit)
admin.site.register(IndicateurProduit)
admin.site.register(Action)
admin.site.register(Activite)


@admin.register(PreuveRealisation)
class PreuveRealisationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_preuve', 'activite', 'uploaded_by', 'created_at')
    list_filter = ('type_preuve', 'created_at')
    search_fields = ('titre', 'activite__titre', 'activite__reference')
    readonly_fields = ('created_at', 'updated_at')

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