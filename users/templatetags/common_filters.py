from datetime import date

from django import template

register = template.Library()


@register.inclusion_tag("cards/includes/pagination.html", takes_context=True)
def pagination(context):
    return {
        'page_obj': context['page_obj'],
        'paginator': context['paginator'],

    }


@register.filter
def alert_class(value):
    alerts = {
        'debug': 'secondary',
        'error': 'danger'
    }
    if value in alerts:
        return alerts.get(value)
    return value


@register.filter
def get_rus_month_year(dt: date) -> str:
    months = [
        'Январь',
        'Февраль',
        'Март',
        'Апрель',
        'Май',
        'Июнь',
        'Июль',
        'Август',
        'Сентябрь',
        'Октябрь',
        'Ноябрь',
        'Декабрь',
    ]

    return f"{months[dt.month - 1]} {dt.year}"
