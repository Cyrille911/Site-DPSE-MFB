# planning/templatetags/planning_filters.py
from django import template
from django_filters import FilterSet, CharFilter, ChoiceFilter 
from ..models import Activite

register = template.Library()

@register.filter
def times(value):
    """Retourne une liste d'entiers de 0 à value-1 pour itérer dans un template."""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return []

@register.filter
def index(value, arg):
    """Retourne l'élément à l'index spécifié dans une liste ou un objet indexable."""
    try:
        return value[int(arg)]
    except (IndexError, ValueError, TypeError):
        return None

@register.filter
def mul(value, arg):
    """Multiplie deux nombres."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def sum_list(value):
    try:
        return sum(float(x) for x in value if x)
    except (TypeError, ValueError):
        return 0.0

@register.filter
def sum_list(value):
    try:
        return sum(float(x) for x in value if x)
    except (TypeError, ValueError):
        return 0.0

@register.filter
def times(n):
    return range(n)

@register.filter
def index(sequence, position):
    return sequence[position]

# Le filtre qui causait l'erreur
class ActiviteFilter(FilterSet):
    status = ChoiceFilter(choices=Activite._meta.get_field('status').choices)
    type = ChoiceFilter(choices=Activite._meta.get_field('type').choices)
    responsable = CharFilter(field_name='responsable__username', lookup_expr='icontains')

    class Meta:
        model = Activite
        fields = ['status', 'type', 'responsable']