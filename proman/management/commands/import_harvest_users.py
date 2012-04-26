from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from proman.models import Profile, Team
from proman.harvest import Harvest

class Command(BaseCommand):
    """
    Imports Users and Teams from Harvest people and departments
    """
    def handle(self, *args, **options):
        total = 0
        data = Harvest().users()
        if data:
            print "Receiving data..."
            for d in data:
                u = d['user']
                try:
                    # try to get the user
                    match = User.objects.get(email=u['email'])
                    print "MATCH!!! ", match
                except:
                    # get team name from department
                    team = Team.objects.get_or_create(name=u['department'])

                    # make the user
                    user = User(
                        email=u['email'],
                        first_name=u['first_name'],
                        last_name=u['last_name'],
                        username=u['email'].replace("@schipul.com",""),
                        date_joined=u['created_at'],
                        is_active=u['is_active'],
                        is_staff=u['is_active'],
                        is_superuser=u['is_admin'])
                    user.save()

                    # update the profile with the team and employee role
                    profile = Profile.objects.get(user=user)
                    profile.team = team[0]
                    profile.role = "employee"
                    profile.save()

                    # if active and admin, assume team leadership
                    if u['is_admin'] and u['is_active']:
                        team[0].leader = user
                        team[0].save()
                    total += 1
            print "Done. Added %s of %s Users" % (total, len(data))
