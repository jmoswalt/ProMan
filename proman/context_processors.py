from proman.models import Profile, Project

def active_users(request):
    return {
        'ACTIVE_USERS': Profile.objects.filter(user__is_active=True).exclude(user__username=request.user.username).order_by('user__last_name'),
        'MY_PROJECTS': Project.objects.filter(version=False, owner__username=request.user.username).order_by('status', 'start_dt')
        }