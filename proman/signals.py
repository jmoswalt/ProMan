from django.db.models import signals
from django.core.cache import cache
from django.conf import settings
from proman.models import Task, Profile

def clear_tasks_cache(sender, instance, created, **kwargs):
    if not created:
        keys = [
            'project.tasks',
            'project.tasks_done',
        ]
        clear_keys = {}
        for key in keys:
            clear_keys[(".".join([settings.SITE_CACHE_KEY, '%s', str(instance.project.pk)]) % key)] = None
        cache.set_many(clear_keys, None)

def clear_profile_cache(sender, instance, **kwargs):
    keys = [
        'profile.get_absolute_url',
        'profile.abbr_name',
    ]
    clear_keys = {}
    for key in keys:
        clear_keys[(".".join([settings.SITE_CACHE_KEY, '%s', str(instance.pk)]) % key)] = None
    cache.set_many(clear_keys, None)

signals.post_save.connect(clear_tasks_cache, sender=Task)
signals.post_delete.connect(clear_tasks_cache, sender=Task)

signals.post_save.connect(clear_profile_cache, sender=Profile)
signals.post_delete.connect(clear_profile_cache, sender=Profile)