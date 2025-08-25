from django.template import Library, Node, TemplateSyntaxError
from django.template.base import token_kwargs
from django.utils.safestring import mark_safe

register = Library()

class SetTagNode(Node):
    def __init__(self, nodelist, key, variables):
        self.nodelist = nodelist
        self.key = key
        self.variables = variables

    def render(self, context):
        key = self.key.resolve(context)

        content = self.nodelist.render(context)

        resolved_variables = {name: var.resolve(context) for name, var in self.variables.items()}

        context.update(resolved_variables)

        if key in context:
            existing_content = context[key]
            if isinstance(existing_content, str):
                context[key] = mark_safe(existing_content + content)
            else:
                context[key] = mark_safe(content)
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
    bits = token.split_contents()

    if len(bits) < 2:
        raise TemplateSyntaxError("'set' tag requires at least one argument (the key name).")

    key = parser.compile_filter(bits[1])

    variables = {}
    if len(bits) > 2 and bits[2] == "with":
        variables = token_kwargs(bits[3:], parser, support_legacy=False)

    nodelist = parser.parse(("endset",))
    parser.delete_first_token()

    return SetTagNode(nodelist, key, variables)
