from django.db.models import signals
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User

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
    profile_clear_keys = []
    profile_keys = [
        'profile.tasks.%s' % SUNDAY_STR,
    ]
    for key in profile_keys:
        profile_clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.owner_id)]) % key))

    profile_project_keys = [
        'profile.projects'
    ]
    for key in profile_project_keys:
        profile_clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.project.owner_id)]) % key))

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
    clear_keys = []

    profile_keys = [
        'profile.projects',
    ]
    for key in profile_keys:
        clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.owner_id)]) % key))

    project_keys = [
        'project.name',
    ]
    for key in project_keys:
        clear_keys.append((".".join([settings.SITE_CACHE_KEY, '%s', str(instance.pk)]) % key))

    cache.delete_many(clear_keys)


def create_first_user_profile(sender, instance, created, **kwargs):
    if created and instance.pk == 1:
        Profile.objects.create(user=instance)


def update_active_user_cache(sender, instance, created, **kwargs):
    key = ".".join([settings.SITE_CACHE_KEY,'active_users'])
    value = Profile.objects.filter(user__is_active=True).order_by('last_name').select_related()
    cache.set(key, value)


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
signals.post_save.connect(create_first_user_profile, sender=User)
signals.post_save.connect(update_active_user_cache, sender=Profile)

###############################
# Signals for Project changes #
###############################

signals.pre_save.connect(clear_project_cache, sender=Project)
signals.post_save.connect(clear_project_cache, sender=Project)
signals.post_delete.connect(clear_project_cache, sender=Project)
