import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def markdownify(text):
    """
    Convertit du Markdown en HTML en utilisant l'extension 'extra' pour enrichir la syntaxe.
    """
    if not text:
        return ""
    html = markdown.markdown(text, extensions=['extra', 'codehilite', 'toc'])
    return mark_safe(html)
