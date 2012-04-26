from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from proman.models import Client, ThirdParty
from proman.sugarcrm import Sugarcrm

class Command(BaseCommand):
    """
    Imports accounts from SugarCRM as Clients in Proman
    """
    def handle(self, *args, **options):
        base_url = getattr(settings, 'SC_URL', None)
        api_user = getattr(settings, 'SC_USER', None)
        api_pass = getattr(settings, 'SC_PASS', None)

        session = Sugarcrm(base_url, api_user, api_pass)

        offset = 0
        result_count = 1
        while result_count > 0:
            accounts = session.get_entry_list('Accounts', offset=offset)
            offset = accounts['next_offset']
            result_count = accounts['result_count']
            for json_data in accounts['entry_list']:
                name = json_data['name_value_list']['name']['value']
                sugar_id = json_data['id']
                try:
                    client = Client.objects.get(name__icontains=name)
                    print "Match !!!", client.name
                    obj, created = ThirdParty.objects.get_or_create(
                        content_type=ContentType.objects.get(model='client'),
                        object_id=client.id,
                        service_item_label='sugarcrm_account_id',
                        service_item_value=sugar_id,
                    )
                except:
                    client = Client(
                        name=name,
                    )
                    client.save()
                    obj, created = ThirdParty.objects.get_or_create(
                        content_type=ContentType.objects.get(model='client'),
                        object_id=client.id,
                        service_item_label='sugarcrm_account_id',
                        service_item_value=sugar_id,
                    )