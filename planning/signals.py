import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


def attribuer_point_focal_responsable(activite):
    """Attribue automatiquement le point_focal et le responsable
    à une activité en fonction de sa structure et de l'entité des utilisateurs."""
    from users.models import User

    if not activite.structure:
        return

    point_focal = User.objects.filter(
        role='point_focal', entity=activite.structure, is_active=True
    ).first()
    responsable = User.objects.filter(
        role='responsable', entity=activite.structure, is_active=True
    ).first()

    updated = False
    if activite.point_focal != point_focal:
        activite.point_focal = point_focal
        updated = True
    if activite.responsable != responsable:
        activite.responsable = responsable
        updated = True

    if updated:
        activite.save(update_fields=['point_focal', 'responsable'])
        logger.debug(
            f"Activite {activite.reference}: point_focal={point_focal}, responsable={responsable}"
        )


@receiver(post_save, sender='planning.Activite')
def on_activite_saved(sender, instance, **kwargs):
    """Quand une activité est créée ou modifiée, attribuer point_focal et responsable."""
    if kwargs.get('update_fields') and set(kwargs['update_fields']) == {'point_focal', 'responsable'}:
        return
    attribuer_point_focal_responsable(instance)


def on_user_saved(sender, instance, **kwargs):
    """Quand un utilisateur point_focal ou responsable est modifié,
    mettre à jour toutes les activités correspondant à son entité."""
    from planning.models import Activite

    if instance.role not in ('point_focal', 'responsable'):
        return

    if not instance.entity:
        return

    activites = Activite.objects.filter(structure=instance.entity)
    for activite in activites:
        attribuer_point_focal_responsable(activite)


def connect_user_signal():
    """Connecte le signal post_save du modèle User.
    Appelé depuis PlanningConfig.ready() pour éviter les imports circulaires."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    post_save.connect(on_user_saved, sender=User)
