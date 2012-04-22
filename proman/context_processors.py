from proman.models import UserMethods, Project

def active_users(request):
    return {
        'ACTIVE_USERS': UserMethods.objects.filter(is_active=True).exclude(username=request.user.username).order_by('last_name'),
        'MY_PROJECTS': Project.objects.filter(version=False, owner__username=request.user.username).order_by('status', 'start_dt')
        }