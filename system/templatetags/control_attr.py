from django import template

register = template.Library()

# Tag to set an attribute of an element (except for 'class')
@register.simple_tag
def set_attribute(element, attribute, value):
    """Set a specific attribute to an element (excluding 'class')."""
    if attribute == 'class':
        raise ValueError("Cannot modify 'class' attribute using set_attribute tag.")
    return f"<{element} {attribute}='{value}'>"

# Tag to remove an attribute from an element (except for 'class')
@register.simple_tag
def remove_attribute(element, attribute):
    """Remove an attribute from an element (excluding 'class')."""
    if attribute == 'class':
        raise ValueError("Cannot modify 'class' attribute using remove_attribute tag.")
    return f"<{element}> <!-- {attribute} attribute removed --> </{element}>"

# Tag to toggle an attribute of an element (except for 'class')
@register.simple_tag
def toggle_attribute(element, attribute, value, condition):
    """Conditionally toggle an attribute on an element (excluding 'class')."""
    if attribute == 'class':
        raise ValueError("Cannot modify 'class' attribute using toggle_attribute tag.")
    if condition:
        return f"<{element} {attribute}='{value}'>"
    return f"<{element}> <!-- {attribute} not applied --> </{element}>"
