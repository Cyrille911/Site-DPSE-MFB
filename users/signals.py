# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

@receiver(post_save, sender='users.User')
def update_activite_responsable(sender, instance, created, **kwargs):
    """
    Met à jour le champ 'responsable' des activités lorsque :
    - Un nouvel utilisateur avec le rôle 'responsable' est créé.
    - Un utilisateur existant change de rôle ou d'entité.
    """
    # Utilisation de apps.get_model pour éviter l'importation directe
    Activite = apps.get_model('planning', 'Activite')

    # Vérifie si l'utilisateur est un responsable (basé sur le champ 'role')
    if instance.role == 'responsable':
        activites = Activite.objects.filter(
            point_focal__entity=instance.entity,
            point_focal__isnull=False
        )
        for activite in activites:
            activite.update_responsable()
            activite.save()

    # Si l'utilisateur n'est plus un responsable ou change d'entité, réévaluer
    elif not created:
        activites = Activite.objects.filter(responsable=instance)
        for activite in activites:
            activite.update_responsable()
            activite.save()