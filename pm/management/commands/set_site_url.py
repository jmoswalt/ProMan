from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    """
    Loads in Clients from Harvest API
    """
    def handle(self, *args, **options):
        if len(args) > 1:
            site_url = args[1]
        else:
            site_url = args[0]

        try:
            site = Site.objects.get(id=int(args[0]))
        except:
            site = Site.objects.all()[0]

        if site:
            site.domain = site_url
            site.name = site_url
            site.save()
            print "Updated the site url to '%s'" % site_url