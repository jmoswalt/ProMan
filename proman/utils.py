from time import strftime
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.core.cache import cache
from django.conf import settings

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
        'assignee_id',
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

def cache_item(value, key=None):
    if key:
        is_set = cache.add(key, value)
        if not is_set:
            cache.set(key, value)
        return cache.get(key)
    return None

