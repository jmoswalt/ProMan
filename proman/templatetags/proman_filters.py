import datetime
from django import template
from django.utils import simplejson as json
from django.contrib.auth.models import User

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

@register.filter
def str_to_json(string):
    try:
        text = json.loads(string)
    except:
        text = ''
    return text

@register.filter
def user_object(pk):
    try:
        user = User.objects.get(pk=pk)
    except:
        return "none"
    return user

@register.filter
def dt_replace(string):
    if "_dt" in string:
        return string.replace("_dt", " date")
    return string.replace("_", " ") 

@register.filter
def render_dt(string):
    return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S')
