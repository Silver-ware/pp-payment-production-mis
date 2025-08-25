from django import template

register = template.Library()

@register.filter
def add(value, arg):
    """Add two numbers"""
    try:
        return value + arg
    except TypeError:
        return ""

@register.filter
def subtract(value, arg):
    """Subtract two numbers"""
    try:
        return value - arg
    except TypeError:
        return ""

@register.filter
def multiply(value, arg):
    """Multiply two numbers"""
    try:
        return value * arg
    except TypeError:
        return ""

@register.filter
def divide(value, arg):
    """Divide two numbers"""
    try:
        if arg == 0:
            return "Cannot divide by zero"
        return value / arg
    except TypeError:
        return ""

@register.filter
def modulus(value, arg):
    """Find modulus (remainder) of division"""
    try:
        return value % arg
    except TypeError:
        return ""

@register.filter
def exponent(value, arg):
    """Raise value to the power of arg"""
    try:
        return value ** arg
    except TypeError:
        return ""

@register.filter
def floor_divide(value, arg):
    """Perform floor division"""
    try:
        return value // arg
    except TypeError:
        return ""
