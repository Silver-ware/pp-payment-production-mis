from django.template import Library

register = Library()

@register.filter
def loop_control(iterable, context):
    for item in iterable:
        context['loop_continue'] = False
        context['loop_break'] = False

        yield item

        if context.get('loop_continue'):
            continue
        if context.get('loop_break'):
            break
