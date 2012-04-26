from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType

from proman.models import Client, ThirdParty
from proman.harvest import Harvest

class Command(BaseCommand):
    """
    Loads in Clients from Harvest API
    """
    def handle(self, *args, **options):
        total = 0
        data = Harvest().clients()
        if data:
            print "Receiving data..."
            for d in data:
                c = d['client']
                try:
                    tp = ThirdParty.objects.get(
                        content_type=ContentType.objects.get(model='client'),
                        service_item_label='harvest_client_id',
                        service_item_value=c['id'],
                    )
                    match = Client.objects.get(id=tp.object_id)
                    print "MATCH!!! ", match
                except:
                    details = c['details']
                    client = Client(
                        name=c['name'],
                        description=details,
                    )
                    client.save()
                    obj, created = ThirdParty.objects.get_or_create(
                        content_type=ContentType.objects.get(model='client'),
                        object_id=client.id,
                        service_item_label='harvest_client_id',
                        service_item_value=c['id'],
                    )
                    total += 1
            print "Done. Added %s of %s Clients" % (total, len(data))
