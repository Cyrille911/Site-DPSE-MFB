import json
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from audit.models import AuditLog


class Command(BaseCommand):
    help = "Exporte les journaux d'audit vers un fichier texte."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help="Nombre de jours à exporter (défaut : 30).",
        )
        parser.add_argument(
            '--output',
            type=str,
            default='logs/audit_export.log',
            help="Chemin du fichier de sortie.",
        )

    def handle(self, *args, **options):
        days = options['days']
        output = options['output']
        since = timezone.now() - timezone.timedelta(days=days)
        logs = AuditLog.objects.filter(timestamp__gte=since).order_by('-timestamp')

        os.makedirs(os.path.dirname(output) or '.', exist_ok=True)

        with open(output, 'w', encoding='utf-8') as f:
            f.write(f"# Export d'audit - {datetime.now().isoformat()} - {logs.count()} lignes\n")
            f.write("# timestamp\taction\tcategory\tuser\tip\tuser_agent\tdescription\textra_data\n")
            for log in logs:
                extra = json.dumps(log.extra_data or {}, ensure_ascii=False)
                line = (
                    f"{log.timestamp.isoformat()}\t"
                    f"{log.action}\t"
                    f"{log.category}\t"
                    f"{log.user or 'anonyme'}\t"
                    f"{log.ip_address or 'n/a'}\t"
                    f"{log.user_agent.replace(chr(9), ' ').replace(chr(10), ' ')}\t"
                    f"{log.description.replace(chr(9), ' ').replace(chr(10), ' ')}\t"
                    f"{extra}\n"
                )
                f.write(line)

        self.stdout.write(
            self.style.SUCCESS(f"{logs.count()} lignes exportées vers {output}")
        )
