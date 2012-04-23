from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from proman.harvest import get_harvest_json

class Command(BaseCommand):
    """
    Clears the entire site cache
    """
    def handle(self, *args, **options):
        api_url = "/people"

        json_data = get_harvest_json(api_url)
        if json_data:
            print "Connected"
            data = [p for p in json_data]
            for d in data:
                for u in d.itervalues():
                    try:
                        match = User.objects.get(email=u['email'])
                        print "MATCH!!! ", match
                    except:
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
            print "Done. Added %s Users" % len(data)