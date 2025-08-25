from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag
def dynamic_url(url_name, *args, **kwargs):
    """
    Resolve a URL dynamically using variables for the name and parameters.
    """
    try:
        return reverse(url_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return ''  # Resturn an unresolve  empty string
