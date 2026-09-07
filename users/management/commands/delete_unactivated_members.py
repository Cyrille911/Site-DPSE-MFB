from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = "Supprime les comptes membres (hors visiteurs) restés inactifs depuis plus de N jours (7 par défaut)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help="Nombre de jours d'inactivité avant suppression (défaut : 7)"
        )

    def handle(self, *args, **options):
        days = options['days']
        count, emails = User.delete_unactivated_members(days=days)
        if count:
            self.stdout.write(self.style.SUCCESS(
                f"{count} compte(s) membre(s) non activé(s) depuis plus de {days} jours supprimé(s) : {', '.join(emails)}"
            ))
        else:
            self.stdout.write(f"Aucun compte à supprimer (délai : {days} jours).")
