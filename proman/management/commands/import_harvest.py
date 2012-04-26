from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    """
    Loads in Clients from Harvest API
    """
    def handle(self, *args, **options):
        print "Importing Users and Teams..."
        call_command('import_harvest_users', **options)
        print "Importing Clients..."
        call_command('import_harvest_clients', **options)
        print "Importing Projects..."
        call_command('import_harvest_projects', **options)