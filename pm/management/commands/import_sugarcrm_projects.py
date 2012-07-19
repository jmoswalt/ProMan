from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from pm.models import Project, ThirdParty
from pm.sugarcrm import Sugarcrm

class Command(BaseCommand):
    """
    Imports projects from SugarCRM as Projects in Proman
    """
    def handle(self, *args, **options):
        base_url = getattr(settings, 'SC_URL', None)
        api_user = getattr(settings, 'SC_USER', None)
        api_pass = getattr(settings, 'SC_PASS', None)

        session = Sugarcrm(base_url, api_user, api_pass)
        modules = session.get_available_modules()
        print modules
        offset = 0
        result_count = 1
        while offset < 50:
            accounts = session.get_entry_list('Project', offset=offset)
            offset = accounts['next_offset']
            result_count = accounts['result_count']
            for json_data in accounts['entry_list']:
                name = json_data['name_value_list']['name']['value']
                date_entered = json_data['name_value_list']['date_entered']['value']
                sugar_id = json_data['id']
                print session.get_relationships(module='Project', module_id=sugar_id, link_field_name='accounts', related_fields=["id"])
                try:
                    project = Project.objects.get(name__icontains=name)
                    print "Match !!!", project.name
                    obj, created = ThirdParty.objects.get_or_create(
                        content_type=ContentType.objects.get(model='project'),
                        object_id=project.id,
                        service_item_label='sugarcrm_project_id',
                        service_item_value=sugar_id,
                    )
                except:
                    project = Project(
                        name=name,
                        owner_id=1,
                        start_dt=date_entered,
                        original_creator_id=1,
                        editor_id=1
                    )
                    project.save()
                    obj, created = ThirdParty.objects.get_or_create(
                        content_type=ContentType.objects.get(model='project'),
                        object_id=project.id,
                        service_item_label='sugarcrm_project_id',
                        service_item_value=sugar_id,
                    )