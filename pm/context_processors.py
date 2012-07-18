from django.core.cache import cache
from django.conf import settings

from pm.utils import get_cached_setting
from pm.models import Profile, Project

def active_users(request):
    return {
        'ACTIVE_USERS': cache.get(".".join([settings.SITE_CACHE_KEY,'active_users']))
        }

def app_settings(request):
    return {
        'NAVBAR_COLOR': get_cached_setting('navbar_color'),
        'SITE_NAME': get_cached_setting('site_name'),
    }