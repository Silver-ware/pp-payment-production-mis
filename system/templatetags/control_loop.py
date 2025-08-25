from django.template import Library, Node, TemplateSyntaxError

register = Library()

class ContinueIfNode(Node):
    def __init__(self, condition):
        self.condition = condition

    def render(self, context):
        if self.condition.resolve(context):
            context['loop_continue'] = True 
        return ""

class BreakIfNode(Node):
    def __init__(self, condition):
        self.condition = condition

    def render(self, context):
        if self.condition.resolve(context):
            context['loop_break'] = True
        return ""

@register.tag(name="continue_if")
def do_continue_if(parser, token):
    try:
        _, condition = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError("`continue_if` tag requires a condition.")
    return ContinueIfNode(parser.compile_filter(condition))

@register.tag(name="break_if")
def do_break_if(parser, token):
    try:
        _, condition = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError("`break_if` tag requires a condition.")
    return BreakIfNode(parser.compile_filter(condition))
