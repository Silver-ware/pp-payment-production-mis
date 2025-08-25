from django.template import Library, Node, TemplateSyntaxError
from django.template.base import token_kwargs
from django.utils.safestring import mark_safe

register = Library()

class SetTagNode(Node):
    def __init__(self, nodelist, key, variables):
        self.nodelist = nodelist  # Captures the inner content between `{% set %}` and `{% endset %}`
        self.key = key            # The context key to set/update
        self.variables = variables  # Additional variables defined in `with`

    def render(self, context):
        # Resolve the key name
        key = self.key.resolve(context)

        # Render the inner content
        content = self.nodelist.render(context)

        # Resolve the additional variables passed with `with`
        resolved_variables = {name: var.resolve(context) for name, var in self.variables.items()}

        # Update the context with the resolved variables
        context.update(resolved_variables)

        # Append or set the HTML content
        if key in context:
            existing_content = context[key]
            if isinstance(existing_content, str):
                context[key] = mark_safe(existing_content + content)
            else:
                context[key] = mark_safe(content)  # Overwrite if existing content is not a string
        else:
            context[key] = mark_safe(content)

        return ""

@register.tag(name="set")
def do_set(parser, token):
    """
    Syntax:
    {% set key [with var1=value1 var2=value2 ...] %}
        HTML or code content here
    {% endset %}
    """
    # Split the token into parts
    bits = token.split_contents()

    if len(bits) < 2:
        raise TemplateSyntaxError("'set' tag requires at least one argument (the key name).")

    # Resolve the key as a variable
    key = parser.compile_filter(bits[1])

    # Parse additional variables passed with `with`
    variables = {}
    if len(bits) > 2 and bits[2] == "with":
        variables = token_kwargs(bits[3:], parser, support_legacy=False)

    # Parse the block content until `{% endset %}`
    nodelist = parser.parse(("endset",))
    parser.delete_first_token()  # Remove `endset`

    return SetTagNode(nodelist, key, variables)
