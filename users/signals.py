# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

@receiver(post_save, sender='users.User')
def update_activite_responsable(sender, instance, created, **kwargs):
    """
    Met à jour les champs 'point_focal' et 'responsable' des activités lorsque :
    - Un nouvel utilisateur avec le rôle 'point_focal' ou 'responsable' est créé.
    - Un utilisateur existant change de rôle ou de structure.
    """
    # Utilisation de apps.get_model pour éviter l'importation directe
    Activite = apps.get_model('planning', 'Activite')

    # Vérifie si l'utilisateur est un point focal ou un responsable
    if instance.role in ['point_focal', 'responsable']:
        # Chercher les activités qui correspondent à la structure de cet utilisateur
        activites = Activite.objects.filter(
            structure=instance.entity,
            structure__isnull=False
        )
        for activite in activites:
            activite.update_responsables()
            activite.save()

    # Si l'utilisateur change de rôle ou de structure, réévaluer toutes les activités
    elif not created:
        # Réévaluer les activités où cet utilisateur était point focal ou responsable
        activites_pf = Activite.objects.filter(point_focal=instance)
        activites_resp = Activite.objects.filter(responsable=instance)
        
        # Combiner les deux querysets sans doublons
        all_activites = activites_pf.union(activites_resp)
        
        for activite in all_activites:
            activite.update_responsables()
            activite.save()
    
    # Mettre à jour toutes les activités pour garantir la cohérence globale
    Activite.update_all_activities_responsables()