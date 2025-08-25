from django.template import Library, Node, TemplateSyntaxError
from django.utils.html import format_html

register = Library()

class OverrideNode(Node):
    def __init__(self, block_name, content=None):
        self.block_name = block_name
        self.content = content

    def render(self, context):
        original_content = context.get(self.block_name, '')

        if self.content:
            return format_html(self.content.render(context))
        return original_content

@register.tag(name="override")
def do_override(parser, token):
    """
    Syntax:
    {% override block_name %}
        Custom content here
    {% endoverride %}
    """
    tokens = token.split_contents()

    if len(tokens) != 2:
        raise TemplateSyntaxError("`override` tag requires a block name.")

    block_name = tokens[1]
    nodelist = parser.parse(('endoverride',))

    return OverrideNode(block_name, nodelist)
