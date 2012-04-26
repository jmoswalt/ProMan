import datetime
from django import template
from django.utils import timezone, simplejson as json
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache

from proman.utils import cache_item

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
            cached = "None"
        cache_item(cached, cache_key)
    return cached

@register.filter
def user_abbr_name(pk):
    key = "profile.abbr_name"
    cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, pk) 
    cached = cache.get(cache_key)
    if cached is None:
        try:
            cached = User.objects.get(pk=pk).profile.abbr_name()
        except:
            cached = "no name"
        cache_item(cached, cache_key)
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
