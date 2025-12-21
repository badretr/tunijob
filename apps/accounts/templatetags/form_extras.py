from django import template

register = template.Library()


@register.filter
def is_textarea(field):
    """Return True if the bound field uses a Textarea widget"""
    try:
        return field.field.widget.__class__.__name__.lower() == 'textarea'
    except AttributeError:
        return False




