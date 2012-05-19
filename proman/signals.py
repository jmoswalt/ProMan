from django.db.models import signals
from django.core.cache import cache
from django.conf import settings
from proman.models import Task, Profile, Project, SUNDAY_STR

def clear_project_tasks_cache(sender, instance, created, **kwargs):
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

def clear_profile_tasks_cache(sender, instance, **kwargs):
    profile_keys = [
        'profile.tasks.%s' % SUNDAY_STR,
    ]
    profile_clear_keys = []
    for key in profile_keys:
        profile_clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.owner_id)]) % key))
    cache.delete_many(profile_clear_keys)

def clear_profile_cache(sender, instance, **kwargs):
    instance_keys = [
        'profile.get_absolute_url',
        'profile.abbr_name',
        'profile.nice_name',
        'profile.client_name',
        'profile.role',
    ]
    model_keys = ['profiles.active_employees', 'profiles.inactive_employees']

    clear_keys = []
    for key in instance_keys:
        clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.pk)]) % key))
    for key in model_keys:
        clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s']) % key))
    cache.delete_many(clear_keys, None)

def clear_project_cache(sender, instance, **kwargs):
    keys = [
        'profile.projects',
    ]
    clear_keys = []
    for key in keys:
        clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.owner_id)]) % key))
    cache.delete_many(clear_keys)


############################
# Signals for Task changes #
############################

signals.post_save.connect(clear_project_tasks_cache, sender=Task)
signals.post_delete.connect(clear_project_tasks_cache, sender=Task)

# pre_save in case a Task is assigned to a new person.
# Need to clear it from the original owner (pre_save) and
# the new owner (post_save). No pre_delete needed since we can't
# reassign and delete at once.
signals.pre_save.connect(clear_profile_tasks_cache, sender=Task)
signals.post_save.connect(clear_profile_tasks_cache, sender=Task)
signals.post_delete.connect(clear_profile_tasks_cache, sender=Task)


###############################
# Signals for Profile changes #
###############################

# No presave, because we don't have owners to worry about
signals.post_save.connect(clear_profile_cache, sender=Profile)
signals.post_delete.connect(clear_profile_cache, sender=Profile)


###############################
# Signals for Project changes #
###############################

signals.pre_save.connect(clear_project_cache, sender=Project)
signals.post_save.connect(clear_project_cache, sender=Project)
signals.post_delete.connect(clear_project_cache, sender=Project)
