from django.db.models import signals
from django.core.cache import cache
from django.conf import settings
from proman.models import Task, Profile, Project

def clear_tasks_cache(sender, instance, created, **kwargs):
    if not created:
        project_keys = [
            'project.tasks',
            'project.tasks_done',
            'project.tasks_not_done',
            'project.tasks_logs',
        ]
        project_clear_keys = []
        for key in project_keys:
            project_clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.project_id)]) % key))
        cache.delete_many(project_clear_keys)

        profile_keys = [
            'profile.week_done_tasks',
            'profile.week_due_tasks',
            'profile.velocity_tasks',
            'profile.total_open_tasks',
        ]
        profile_clear_keys = []
        for key in profile_keys:
            profile_clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.assignee_id)]) % key))
        cache.delete_many(profile_clear_keys)

def clear_profile_tasks_cache(sender, instance, **kwargs):
    profile_keys = [
        'profile.week_done_tasks',
        'profile.week_due_tasks',
        'profile.velocity_tasks',
        'profile.total_open_tasks',
    ]
    profile_clear_keys = []
    for key in profile_keys:
        profile_clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.assignee_id)]) % key))
    cache.delete_many(profile_clear_keys)

def clear_profile_cache(sender, instance, **kwargs):
    keys = [
        'profile.get_absolute_url',
        'profile.abbr_name',
        'profile.nice_name',
        'profile.client_name',
    ]
    clear_keys = []
    for key in keys:
        clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.pk)]) % key))
    cache.delete_many(clear_keys, None)

def clear_project_cache(sender, instance, **kwargs):
    keys = [
        'profile.open_projects',
        'profile.done_projects',
    ]
    clear_keys = []
    for key in keys:
        clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.owner_id)]) % key))
    cache.delete_many(clear_keys)

signals.post_save.connect(clear_tasks_cache, sender=Task)
signals.pre_save.connect(clear_profile_tasks_cache, sender=Task)
signals.post_delete.connect(clear_tasks_cache, sender=Task)

signals.post_save.connect(clear_profile_cache, sender=Profile)
signals.post_delete.connect(clear_profile_cache, sender=Profile)

signals.post_save.connect(clear_project_cache, sender=Project)
signals.post_delete.connect(clear_project_cache, sender=Project)
