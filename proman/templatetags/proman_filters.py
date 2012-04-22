import datetime
from django import template

register = template.Library()

@register.filter
def avg_start_date(projects):
    """ converts an average datetime to a number days """
    days = []
    for p in projects:
        days.append(p.age())
    average = sum(days)/len(days)
    today = datetime.datetime.now()
    delta = datetime.timedelta(days=average)
    return today - delta