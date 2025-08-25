from django.template import Library, Template, TemplateSyntaxError
from django.template.loader import get_template

register = Library()

@register.simple_tag(takes_context=True)
def include_with(context, template_name, data=None):
    """
    Renders a template with additional context provided as a dictionary.

    Usage:
        {% include_with "template_name.html" data={'key': value} %}
    """
    if not template_name:
        raise TemplateSyntaxError("The 'include_with' tag requires a template name.")

    template = get_template(template_name)

    if data:
        new_context = context.flatten()
        new_context.update(data)
    else:
        new_context = context.flatten()

    return template.render(new_context)
