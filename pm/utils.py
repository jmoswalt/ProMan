from time import strftime
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.core.cache import cache
from django.conf import settings

from pm.models import Setting

def get_change_message(old, new, fields):
    if old and new and fields:
        output = []
        for field in fields:
            if getattr(old, field) != getattr(new, field):
                output.append({
                    "field": field,
                    "old": getattr(old, field),
                    "new": getattr(new, field),
                })

        if not output:
            return "made no changes"
        return json.dumps(output, cls=DjangoJSONEncoder)
    return "made no changes"

def get_task_change_message(old=None, new=None):
    fields = (
        'title',
        'description',
        'owner_id',
        'due_dt',
        'task_time',
        'completed',
        'completed_dt',
        'stuck',
        'resolution',
        'private',
        'billable',
    )
    return get_change_message(old, new, fields)

def get_project_change_message(old=None, new=None):
    fields = (
        'name',
        'description',
        'owner_id',
        'start_dt',
        'end_dt',
        'task_budget',
        'technology',
        'status',
        'ongoing',
    )
    return get_change_message(old, new, fields)

def get_profile_change_message(old=None, new=None):
    fields = (
        'first_name',
        'last_name',
        'email',
        'phone',
        'title',
        'team_id',
        'team_leader',
        'client_id',
    )
    return get_change_message(old, new, fields)


def get_cached_setting(key):
    prekey = "app_setting"
    cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, prekey, key) 
    cached = cache.get(cache_key)
    if cached is None:
        try:
            cached = Setting.objects.get(slug=key).value
            if cached is None:
                cached = ""
        except:
            cached = ""
        cache.set(cache_key, cached)
    return cached
