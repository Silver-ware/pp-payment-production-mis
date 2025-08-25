from django import template

register = template.Library()

# Tag to add a class to an element
@register.simple_tag
def add_class(element, class_name):
    """Add a class to an element."""
    return f"<{element} class='{class_name}'>"

# Tag to remove a class from an element
@register.simple_tag
def remove_class(element, class_name):
    """Remove a class from an element."""
    return f"<{element}> <!-- {class_name} class removed --> </{element}>"

# Tag to toggle a class on an element
@register.simple_tag
def toggle_class(element, class_name, condition):
    """Conditionally toggle a class on an element."""
    if condition:
        return f"<{element} class='{class_name}'>"
    return f"<{element}> <!-- {class_name} class not applied --> </{element}>"
