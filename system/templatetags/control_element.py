from django import template

register = template.Library()

# Tag to create or replace an HTML element
@register.simple_tag
def replace_element(tag_name, content):
    """Replace the content of an HTML element."""
    return f"<{tag_name}>{content}</{tag_name}>"

# Tag to delete an HTML element
@register.simple_tag
def delete_element(tag_name):
    """Delete an HTML element by removing its tag."""
    return f"<!-- {tag_name} element removed -->"

# Tag to toggle the visibility of an element (simulating JS-like behavior)
@register.simple_tag
def toggle_element_visibility(is_visible):
    """Toggle the visibility of an HTML element."""
    return 'display: none;' if not is_visible else 'display: block;'

# Tag to append content to an element
@register.simple_tag
def append_to_element(element, additional_content):
    """Append content to an existing element."""
    return f"<{element}>{additional_content}</{element}>"
