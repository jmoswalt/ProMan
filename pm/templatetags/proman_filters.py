import datetime
from django import template
from django.utils import timezone, simplejson as json
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache

from pm.models import Task

register = template.Library()

@register.filter
def avg_start_date(projects):
    """ converts an average datetime to a number days """
    days = []
    for p in projects:
        days.append(p.age())
    average = 0
    if len(days) > 0:
        average = sum(days)/len(days)
    today = timezone.now()
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
    key = "user"
    cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, pk) 
    cached = cache.get(cache_key)
    if cached is None:
        try:
            cached = User.objects.get(pk=pk)
        except:
            cached = ""
        cache.set(cache_key, cached)
    return cached

@register.filter
def task_name(pk):
    key = "task"
    cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, pk) 
    cached = cache.get(cache_key)
    if cached is None:
        try:
            cached = Task.objects.get(pk=pk)
        except:
            cached = ""
        cache.set(cache_key, cached)
    return cached.title

@register.filter
def user_abbr_name(pk):
    key = "profile.abbr_name"
    cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, pk) 
    cached = cache.get(cache_key)
    if cached is None:
        try:
            cached = User.objects.get(pk=pk).profile.abbr_name()
        except:
            cached = ""
        cache.set(cache_key, cached)
    return cached

@register.filter
def dt_replace(string):
    if "_dt" in string:
        return string.replace("_dt", " date")
    return string.replace("_", " ") 

@register.filter
def render_dt(string):
    if string:
        return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%SZ')
    return "None"

@register.filter
def action_flag_text(af):
    if af == 1:
        return "added"
    elif af == 5:
        return "closed"
    else:
        return "missed deadline for"