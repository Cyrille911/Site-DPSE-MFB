from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')

def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return ''
    
@register.filter
def split(value, delimiter):
    return value.split(delimiter)