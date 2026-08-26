from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def delete_unactivated_members_task():
    """Tâche périodique : supprime les comptes membres non activés depuis plus de 7 jours."""
    from .models import User
    count, emails = User.delete_unactivated_members(days=7)
    if count:
        logger.info(
            "[AutoCleanup] %s compte(s) membre(s) non activé(s) supprimé(s) après 7 jours : %s",
            count, ", ".join(emails)
        )
    return count
