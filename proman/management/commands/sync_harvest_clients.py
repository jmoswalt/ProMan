from django.core.management.base import BaseCommand, CommandError

from proman.models import Client
from proman.harvest import get_harvest_json

class Command(BaseCommand):
    """
    Loads in Clients from Harvest API
    """
    def handle(self, *args, **options):
        api_url = "/clients"
        json_data = get_harvest_json(api_url)
        if json_data:
            print "Connected"
            data = [p for p in json_data]
            for d in data:
                for client in d.itervalues():
                    try:
                        match = Client.objects.get(harvest_client_id=client['id'])
                        print "MATCH!!! ", match
                    except:
                        client = Client(
                            name=client['name'],
                            harvest_client_id=client['id'],
                        )
                        client.save()
            print "Done. Added %s Users" % len(data)
