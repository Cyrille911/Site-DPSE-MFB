import io
import uuid
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from docx import Document
from docx.shared import Inches

from planning.models import Activite, PlanAction, QuarterlyReport


@shared_task
def check_activity_alerts_task():
    Activite.check_activity_alerts()


User = get_user_model()


def _build_report_doc(plan, annee, trimestre, activites_trimestre):
    doc = Document()
    annee_index = annee - plan.annee_debut

    doc.add_heading(f'Rapport trimestriel {trimestre} {annee}', level=0)
    doc.add_heading(f'Plan d\'actions : {plan.titre} ({plan.reference})', level=1)
    doc.add_paragraph(f'Date de génération : {datetime.now().strftime("%d/%m/%Y %H:%M")}')

    # Résumé global
    doc.add_heading('1. Résumé global', level=1)
    total = len(activites_trimestre)
    par_statut = {}
    for a in activites_trimestre:
        s = a.status[annee_index] if a.status and len(a.status) > annee_index else 'Non entamée'
        par_statut[s] = par_statut.get(s, 0) + 1

    resumé = doc.add_paragraph()
    resumé.add_run(f'Nombre d\'activités concernées par {trimestre} : {total}\n')
    for s, c in par_statut.items():
        resumé.add_run(f'  - {s} : {c}\n')

    # Synthèse financière
    doc.add_heading('2. Synthèse financière', level=1)
    total_cout = sum(float(a.couts[annee_index] or 0) for a in activites_trimestre if a.couts and len(a.couts) > annee_index)
    doc.add_paragraph(f'Coût total des activités du trimestre : {total_cout:,.2f}')

    table = doc.add_table(rows=1, cols=3)
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = 'Structure'
    hdr[1].text = 'Coût'
    hdr[2].text = 'Activités'

    by_entity = {}
    for a in activites_trimestre:
        e = (a.point_focal.entity if a.point_focal and getattr(a.point_focal, 'entity', None) else
             a.responsable.entity if a.responsable and getattr(a.responsable, 'entity', None) else 'Sans entité')
        c = by_entity.setdefault(e, {'cout': 0.0, 'count': 0})
        c['count'] += 1
        c['cout'] += float(a.couts[annee_index] or 0) if a.couts and len(a.couts) > annee_index else 0.0

    for e, c in sorted(by_entity.items()):
        row = table.add_row().cells
        row[0].text = e
        row[1].text = f"{c['cout']:,.2f}"
        row[2].text = str(c['count'])

    # Activités du trimestre
    doc.add_heading('3. Activités du trimestre', level=1)
    table = doc.add_table(rows=1, cols=7)
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = 'Référence'
    hdr[1].text = 'Titre'
    hdr[2].text = 'Structure'
    hdr[3].text = 'Cible'
    hdr[4].text = 'Réalisation'
    hdr[5].text = 'Statut'
    hdr[6].text = 'Coût'

    for a in activites_trimestre:
        e = (a.point_focal.entity if a.point_focal and getattr(a.point_focal, 'entity', None) else
             a.responsable.entity if a.responsable and getattr(a.responsable, 'entity', None) else 'Sans entité')
        row = table.add_row().cells
        row[0].text = a.reference or ''
        row[1].text = a.titre or ''
        row[2].text = e
        row[3].text = a.cibles[annee_index] if a.cibles and len(a.cibles) > annee_index else ''
        row[4].text = a.realisation[annee_index] if a.realisation and len(a.realisation) > annee_index else ''
        row[5].text = a.status[annee_index] if a.status and len(a.status) > annee_index else 'Non entamée'
        row[6].text = f"{float(a.couts[annee_index] or 0):,.2f}" if a.couts and len(a.couts) > annee_index else '0.00'

    return doc


@shared_task
def generate_quarterly_report(plan_id, annee, trimestre, user_id=None):
    plan = PlanAction.objects.get(id=plan_id)
    annee_index = annee - plan.annee_debut
    if annee_index < 0 or annee_index >= plan.horizon:
        raise ValueError("Année hors de l'horizon du plan.")

    activites = Activite.objects.filter(
        action__produit__effet__plan=plan
    ).select_related('action__produit__effet', 'point_focal', 'responsable')

    activites_trimestre = []
    for a in activites:
        if not a.periodes_execution or len(a.periodes_execution) <= annee_index:
            continue
        if trimestre in a.periodes_execution[annee_index]:
            activites_trimestre.append(a)

    doc = _build_report_doc(plan, annee, trimestre, activites_trimestre)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    content = buffer.read()

    filename = f"rapport_{plan.reference}_{annee}_{trimestre}_{uuid.uuid4().hex[:8]}.docx"

    report, _ = QuarterlyReport.objects.get_or_create(
        plan=plan,
        annee=annee,
        trimestre=trimestre,
        defaults={'generated_by_id': user_id, 'recipients_emails': []}
    )

    if report.fichier:
        report.fichier.delete(save=False)

    report.fichier.save(filename, ContentFile(content), save=True)
    report.generated_by_id = user_id

    # Destinataires : acteurs du plan
    recipients = set()
    for a in activites_trimestre:
        if a.point_focal and a.point_focal.email:
            recipients.add(a.point_focal.email)
        if a.responsable and a.responsable.email:
            recipients.add(a.responsable.email)
    for u in User.objects.filter(is_active=True, groups__name='SuiveurEvaluateur'):
        if u.email:
            recipients.add(u.email)

    report.recipients_emails = sorted(recipients)
    report.save(update_fields=['recipients_emails', 'generated_by'])

    if recipients:
        email = EmailMessage(
            subject=f"Rapport trimestriel {trimestre} {annee} - {plan.reference}",
            body=f"Veuillez trouver ci-joint le rapport trimestriel {trimestre} {annee} du plan {plan.reference}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=list(recipients),
        )
        email.attach_file(report.fichier.path)
        email.send(fail_silently=True)

    return report.id
