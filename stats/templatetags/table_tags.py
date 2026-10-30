from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')


@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError, KeyError):
        return ''


@register.filter
def split(value, delimiter):
    return str(value).split(delimiter)
