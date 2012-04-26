from django.core.cache import cache
from django.conf import settings

from proman.models import Profile, Project

def active_users(request):
    return {
        'ACTIVE_USERS': cache.get(".".join([settings.SITE_CACHE_KEY,'active_users']))
        }