from time import strftime
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json

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
        'status',
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
