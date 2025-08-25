from django import template

register = template.Library()

@register.simple_tag
def add_tag(value, arg):
    """Add two numbers"""
    try:
        return value + arg
    except TypeError:
        return None

@register.simple_tag
def subtract_tag(value, arg):
    """Subtract two numbers"""
    try:
        return value - arg
    except TypeError:
        return None

@register.simple_tag
def multiply_tag(value, arg):
    """Multiply two numbers"""
    try:
        return value * arg
    except TypeError:
        return None

@register.simple_tag
def divide_tag(value, arg):
    """Divide two numbers"""
    try:
        if arg == 0:
            return "Cannot divide by zero"
        return value / arg
    except TypeError:
        return None

@register.simple_tag
def modulus_tag(value, arg):
    """Find modulus (remainder) of division"""
    try:
        return value % arg
    except TypeError:
        return None

@register.simple_tag
def exponent_tag(value, arg):
    """Raise value to the power of arg"""
    try:
        return value ** arg
    except TypeError:
        return None

@register.simple_tag
def floor_divide_tag(value, arg):
    """Perform floor division"""
    try:
        return value // arg
    except TypeError:
        return None
