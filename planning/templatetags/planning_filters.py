from django import template
from django_filters import FilterSet, CharFilter, ChoiceFilter
from ..models import Activite

register = template.Library()

# Filtres pour les templates
@register.filter
def times(value):
    """Retourne une plage de valeurs de 0 à value-1 pour les boucles en template."""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return []

@register.filter
def index(sequence, position):
    """Retourne l'élément à l'index donné dans une liste ou None si hors limite."""
    try:
        return sequence[int(position)]
    except (IndexError, ValueError, TypeError):
        return None

@register.filter
def mul(value, arg):
    """Multiplie deux nombres et retourne le résultat."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value  # Retourne la valeur originale en cas d'erreur

@register.filter
def sum_list(value):
    """Retourne la somme des éléments numériques d'une liste."""
    try:
        return sum(float(x) for x in value if x)
    except (TypeError, ValueError):
        return 0.0

# Filtres pour le filtrage de queryset
@register.filter
def filter_by_effet(queryset, effet):
    """Filtre un queryset par effet."""
    return queryset.filter(effet=effet)

@register.filter
def filter_by_produit(queryset, produit):
    """Filtre un queryset par produit."""
    return queryset.filter(produit=produit)

@register.filter
def filter_by_action(queryset, action):
    """Filtre un queryset par action."""
    return queryset.filter(action=action)

@register.filter
def filter_by_structure(queryset, structure):
    """Filtre un queryset par structure."""
    return queryset.filter(structure=structure)

# Filtre DjangoFilterSet pour le modèle Activite
class ActiviteFilter(FilterSet):
    status = ChoiceFilter(choices=Activite._meta.get_field('status').choices)
    type = ChoiceFilter(choices=Activite._meta.get_field('type').choices)
    structure = CharFilter(field_name='structure', lookup_expr='icontains')
    responsable = CharFilter(field_name='responsable__username', lookup_expr='icontains')

    class Meta:
        model = Activite
        fields = ['status', 'type', 'structure', 'responsable']