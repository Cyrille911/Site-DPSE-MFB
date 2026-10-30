import json
from django.contrib import admin
from .models import PlanAction, Axe, Effet, IndicateurEffet, Produit, IndicateurProduit, Action, Activite, ActiviteLog, PreuveRealisation, QuarterlyReport

# Enregistrer chaque modèle dans l'admin
admin.site.register(PlanAction)


@admin.register(Axe)
class AxeAdmin(admin.ModelAdmin):
    list_display = ('reference', 'titre', 'plan', 'nombre_effets', 'nombre_produits', 'nombre_actions', 'nombre_activites')
    list_filter = ('plan',)
    search_fields = ('titre', 'reference')


@admin.register(Effet)
class EffetAdmin(admin.ModelAdmin):
    list_display = ('reference', 'titre', 'axe', 'nombre_produits', 'nombre_actions', 'nombre_activites')
    list_filter = ('axe__plan', 'axe')
    search_fields = ('titre', 'reference')


admin.site.register(IndicateurEffet)
admin.site.register(Produit)
admin.site.register(IndicateurProduit)
admin.site.register(Action)


class PreuveRealisationInline(admin.TabularInline):
    model = PreuveRealisation
    extra = 0
    fields = ('annee', 'type', 'description', 'fichier', 'url', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display = ('reference', 'titre', 'type', 'structure', 'point_focal', 'responsable')
    list_filter = ('type', 'structure', 'action__produit__effet__axe__plan')
    search_fields = ('titre', 'reference', 'indicateur_label')
    inlines = [PreuveRealisationInline]


@admin.register(PreuveRealisation)
class PreuveRealisationAdmin(admin.ModelAdmin):
    list_display = ('description', 'type', 'activite', 'annee', 'uploaded_by', 'uploaded_at')
    list_filter = ('type', 'annee', 'uploaded_at')
    search_fields = ('description', 'activite__titre', 'activite__reference')
    readonly_fields = ('uploaded_at',)


@admin.register(QuarterlyReport)
class QuarterlyReportAdmin(admin.ModelAdmin):
    list_display = ('plan', 'annee', 'trimestre', 'generated_by', 'generated_at')
    list_filter = ('annee', 'trimestre')

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