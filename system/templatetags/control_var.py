from django import template

register = template.Library()

# Tag to update a variable in the template
@register.simple_tag
def set_variable(var_name, value):
    """Set a template variable to a specified value."""
    return f"{var_name} = {value}"

# Tag to delete a variable in the template
@register.simple_tag
def delete_variable(var_name):
    """Delete a template variable (not really deleting, just ignoring it)."""
    return f"<!-- {var_name} deleted -->"

# Tag to get the value of a variable
@register.simple_tag
def get_variable(var_name, context):
    """Retrieve a variable's value from the context."""
    return context.get(var_name, None)

# Tag to check if a variable exists in the template context
@register.simple_tag
def var_exists(var_name, context):
    """Check if a variable exists in the template context."""
    return var_name in context
