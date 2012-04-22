from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

class Command(BaseCommand):
    """
    Clears the entire site cache
    """
    def handle(self, *args, **options):
        from django.conf import settings
        from harvest import Harvest
        print "Trying to connect... "
        try:
            h_conn = Harvest(settings.HV_URL, settings.HV_USER, settings.HV_PASS)
        except:
            h_conn = None
        if not h_conn:
            print "Missing or invalid settings to connect"
        else:
            print "Got connected"
            for u in h_conn.users():
                print u.email
                try:
                    match = User.objects.get(email=u.email)
                    print "MATCH!!! ", match
                except:
                    user = User(
                        email=u.email,
                        first_name=u.first_name,
                        last_name=u.last_name,
                        username=u.email,
                        date_joined=u.created_at,
                        is_active=u.active,
                        is_staff=1,
                        is_superuser=u.is_admin)
                    user.save()