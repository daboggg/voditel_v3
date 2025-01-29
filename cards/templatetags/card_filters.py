from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def round3(value):
    return round(Decimal(value), 3).normalize()