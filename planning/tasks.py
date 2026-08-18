import io
import uuid
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt, RGBColor

from planning.models import Activite, PlanAction, QuarterlyReport


@shared_task
def check_activity_alerts_task():
    Activite.check_activity_alerts()


User = get_user_model()


def _set_run_font(run, name='Arial', size=11, bold=False, italic=False, color=None):
    font = run.font
    font.name = name
    font.size = Pt(size)
    font.bold = bold
    font.italic = italic
    run._element.rPr.rFonts.set(qn('w:ascii'), name)
    run._element.rPr.rFonts.set(qn('w:hAnsi'), name)
    if color:
        font.color.rgb = color


def _set_cell_shading(cell, color_hex):
    cell._tc.get_or_add_tcPr().append(
        parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), color_hex))
    )


CIV_ORANGE = RGBColor(0xFF, 0x9A, 0x00)
CIV_GREEN = RGBColor(0x00, 0x96, 0x39)
CIV_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CIV_BLACK = RGBColor(0x00, 0x00, 0x00)


def _build_report_doc(plan, annee, trimestre, activites_trimestre):
    annee_index = annee - plan.annee_debut

    doc = Document()

    # Police par défaut
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    style._element.rPr.rFonts.set(qn('w:ascii'), 'Arial')
    style._element.rPr.rFonts.set(qn('w:hAnsi'), 'Arial')

    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)

    # En-tête : drapeau tricolore + éléments institutionnels
    header = section.header
    header_table = header.add_table(rows=1, cols=3, width=Inches(6.5))
    header_table.autofit = False
    for i, width in enumerate([2.17, 2.17, 2.17]):
        header_table.columns[i].width = Inches(width)
    flag_cells = header_table.rows[0].cells
    _set_cell_shading(flag_cells[0], 'FF9A00')
    _set_cell_shading(flag_cells[1], 'FFFFFF')
    _set_cell_shading(flag_cells[2], '009639')
    for cell in flag_cells:
        p = cell.paragraphs[0]
        p.add_run(' ')

    header_para = header.add_paragraph()
    header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_run_font(
        header_para.add_run('Document officiel - DPSE MFB'),
        size=8,
        color=RGBColor(0x66, 0x66, 0x66)
    )

    # Pied de page
    footer = section.footer
    footer_para = footer.paragraphs[0]
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run_font(
        footer_para.add_run(f'Rapport généré le {datetime.now().strftime("%d/%m/%Y")}'),
        size=8,
        color=RGBColor(0x66, 0x66, 0x66)
    )

    # Page de garde institutionnelle
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run_font(p.add_run('RÉPUBLIQUE DE CÔTE D\'IVOIRE'), size=18, bold=True, color=CIV_GREEN)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run_font(p.add_run('Union - Discipline - Travail'), size=11, italic=True, color=CIV_ORANGE)

    # Bande tricolore décorative sous le titre
    band = doc.add_table(rows=1, cols=3)
    band.width = Inches(6.0)
    band.alignment = WD_TABLE_ALIGNMENT.CENTER
    band.autofit = False
    for i, width in enumerate([2.0, 2.0, 2.0]):
        band.columns[i].width = Inches(width)
    band_cells = band.rows[0].cells
    _set_cell_shading(band_cells[0], 'FF9A00')
    _set_cell_shading(band_cells[1], 'FFFFFF')
    _set_cell_shading(band_cells[2], '009639')
    for cell in band_cells:
        p = cell.paragraphs[0]
        p.add_run(' ')

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run_font(p.add_run('MINISTÈRE DES FINANCES ET DU BUDGET'), size=14, bold=True, color=CIV_ORANGE)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run_font(p.add_run('Direction du Pilotage et du Suivi-Évaluation'), size=12, bold=True)

    for _ in range(4):
        doc.add_paragraph()

    # Titre principal du document
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run_font(p.add_run(f'RAPPORT TRIMESTRIEL {trimestre} {annee}'), size=20, bold=True, color=CIV_GREEN)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run_font(p.add_run(f'Plan d\'actions : {plan.titre} ({plan.reference})'), size=13, bold=True)

    # 1. Résumé global
    h = doc.add_heading('1. Résumé global', level=1)
    _set_run_font(h.runs[0], size=14, bold=True, color=CIV_GREEN)

    total = len(activites_trimestre)
    par_statut = {}
    for a in activites_trimestre:
        s = a.status[annee_index] if a.status and len(a.status) > annee_index else 'Non entamée'
        par_statut[s] = par_statut.get(s, 0) + 1

    p = doc.add_paragraph()
    _set_run_font(
        p.add_run(f'Nombre d\'activités concernées par {trimestre} : {total}'),
        bold=True
    )
    for s, c in par_statut.items():
        p = doc.add_paragraph(style='List Bullet')
        _set_run_font(p.add_run(f'{s} : {c}'))

    # 2. Synthèse financière
    h = doc.add_heading('2. Synthèse financière', level=1)
    _set_run_font(h.runs[0], size=14, bold=True, color=CIV_GREEN)

    total_cout = sum(float(a.couts[annee_index] or 0) for a in activites_trimestre if a.couts and len(a.couts) > annee_index)
    p = doc.add_paragraph()
    _set_run_font(
        p.add_run(f'Coût total des activités du trimestre : {total_cout:,.2f}'),
        bold=True
    )

    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text = 'Structure'
    hdr[1].text = 'Coût'
    hdr[2].text = 'Activités'
    for cell in hdr:
        _set_cell_shading(cell, '009639')
        for r in cell.paragraphs[0].runs:
            _set_run_font(r, bold=True, color=CIV_WHITE)

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

    # 3. Activités du trimestre
    h = doc.add_heading('3. Activités du trimestre', level=1)
    _set_run_font(h.runs[0], size=14, bold=True, color=CIV_GREEN)

    table = doc.add_table(rows=1, cols=7)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    cols = ['Référence', 'Titre', 'Structure', 'Cible', 'Réalisation', 'Statut', 'Coût']
    for i, text in enumerate(cols):
        hdr[i].text = text
        _set_cell_shading(hdr[i], 'FF9A00')
        for r in hdr[i].paragraphs[0].runs:
            _set_run_font(r, bold=True, color=CIV_BLACK)

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
