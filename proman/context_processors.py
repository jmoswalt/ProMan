from proman.models import UserMethods

def active_users(request):
    return {'ACTIVE_USERS': UserMethods.objects.filter(is_active=True).order_by('last_name')}