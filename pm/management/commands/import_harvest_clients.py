from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone

from pm.models import Client, ThirdParty, ContentImport
from pm.harvest import Harvest

class Command(BaseCommand):
    """
    Loads in Clients from Harvest API
    """
    def handle(self, *args, **options):
        total = 0
        ci = None
        try:
            content_import_pk = args[0]
        except:
            content_import_pk = None
        if content_import_pk:
            ci = get_object_or_404(ContentImport, pk=content_import_pk)
        data = Harvest().clients()
        if data:
            if ci:
                cache.set(('content_import.total.%s') % ci.pk, len(data))
                cache.set(('content_import.matched.%s') % ci.pk, 0)
                cache.set(('content_import.added.%s') % ci.pk, 0)
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
                    if ci:
                        cache.incr(('content_import.matched.%s') % ci.pk)
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
                    if ci:
                        cache.incr(('content_import.added.%s') % ci.pk)
                    total += 1
            print "Done. Added %s of %s Clients" % (total, len(data))
        if ci:
            ci.complete_dt = timezone.now()
            cache.set(('content_import.complete_dt.%s') % ci.pk, ci.complete_dt)
            ci.matched = cache.get(('content_import.matched.%s') % ci.pk)
            ci.added = cache.get(('content_import.added.%s') % ci.pk)
            ci.estimated_total = cache.get(('content_import.total.%s') % ci.pk)
            ci.save()
