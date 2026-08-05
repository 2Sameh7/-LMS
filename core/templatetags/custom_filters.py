from django import template

register = template.Library()

@register.filter
def sum_attr(value, arg):
    """جمع قيمة خاصية من قائمة كائنات"""
    try:
        return sum(getattr(obj, arg, 0) or 0 for obj in value)
    except (TypeError, AttributeError):
        return 0

@register.filter
def avg_attr(value, arg):
    """متوسط قيمة خاصية من قائمة كائنات"""
    try:
        values = [getattr(obj, arg) for obj in value if getattr(obj, arg)]
        return sum(values) / len(values) if values else 0
    except (TypeError, AttributeError):
        return 0