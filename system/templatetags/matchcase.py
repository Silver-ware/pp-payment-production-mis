from django.template import Library, Node, TemplateSyntaxError

register = Library()

class MatchNode(Node):
    def __init__(self, variable_name, cases):
        self.variable_name = variable_name
        self.cases = cases

    def render(self, context):
        try:
            value = context[self.variable_name]
        except KeyError:
            raise TemplateSyntaxError(f"Variable '{self.variable_name}' not found in context.")

        for pattern, nodelist in self.cases:
            if pattern == "_":
                return nodelist.render(context)
            if str(value) == pattern:
                return nodelist.render(context)

        return ""

@register.tag(name="match")
def do_match(parser, token):
    """
    Syntax:
    {% match variable %}
        {% case "pattern1" %}
            Content for pattern1
        {% case "pattern2" %}
            Content for pattern2
        {% case _ %}
            Default content
    {% endmatch %}
    """
    tokens = token.split_contents()
    if len(tokens) != 2:
        raise TemplateSyntaxError("`match` tag requires a variable name.")

    variable_name = tokens[1]
    cases = []

    # Parse until endmatch
    while True:
        token = parser.next_token()
        if token.contents.startswith("case"):
            parts = token.contents.split(maxsplit=1)
            if len(parts) != 2:
                raise TemplateSyntaxError("`case` tag requires a pattern.")

            pattern = parts[1].strip('"').strip("'")
            nodelist = parser.parse(("case", "endmatch"))
            cases.append((pattern, nodelist))

            if parser.next_token().contents == "endmatch":
                break
        else:
            raise TemplateSyntaxError("`match` tag must be closed with `endmatch`.")

    return MatchNode(variable_name, cases)
