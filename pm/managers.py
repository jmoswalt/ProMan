from django.db import models
from django.conf import settings
from django.core.cache import cache

class VersionManager(models.Manager):
    def get_query_set(self):
        return super(VersionManager, self).get_query_set().filter(version=False)

class TaskManager(VersionManager):
    def owner_id(self, id):
        return self.get_query_set().filter(owner_id=id)

    def project_id(self, id):
        return self.get_query_set().filter(project_id=id)


class ProjectManager(VersionManager):
    """
    Manager used for Projects to filter out non-active versions.
    """

    def owner_id(self, id):
        return self.get_query_set().filter(owner_id=id)

    def client_id(self, id):
        return self.get_query_set().filter(client_id=id)


class ProfileManager(models.Manager):

    def active_employees(self):
        key = "profiles.active_employees"
        cache_key = "%s.%s" % (settings.SITE_CACHE_KEY, key) 
        cached = cache.get(cache_key)
        if cached is None:
            cached = self.get_query_set().filter(user__is_active=True, user__is_staff=True).order_by('last_name')
            cache.set(cache_key, cached)
        return cached

    def inactive_employees(self):
        key = "profiles.inactive_employees"
        cache_key = "%s.%s" % (settings.SITE_CACHE_KEY, key) 
        cached = cache.get(cache_key)
        if cached is None:
            cached = self.get_query_set().filter(user__is_active=False, user__is_staff=True).order_by('last_name')
            cache.set(cache_key, cached)
        return cached

    def admins(self):
        return self.get_query_set().filter(user__is_active=True, user__is_superuser=True).order_by('last_name')
