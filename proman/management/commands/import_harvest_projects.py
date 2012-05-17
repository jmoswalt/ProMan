from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils import timezone

from proman.models import Client, Project, ThirdParty, Profile, ContentImport
from proman.harvest import Harvest

class Command(BaseCommand):
    """
    Loads in Projects from Harvest API
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
        data = Harvest().projects()
        if data:
            if ci:
                # divide by 3 because of Lost Time and Client Services projects
                cache.set(('content_import.total.%s') % ci.pk, round(len(data)/3))
                cache.set(('content_import.matched.%s') % ci.pk, 0)
                cache.set(('content_import.added.%s') % ci.pk, 0)
            print "Receiving data..."
            for d in data:
                p = d['project']
                if p['name'] != "Lost Time" and p['name'] != "Client Services":
                    try:
                        project_match = ThirdParty.objects.get(
                            service_item_value=p['id'],
                            service_item_label="harvest_project_id",
                            content_type=ContentType.objects.get(model='project')
                        )
                        match = Project.objects.get(id=project_match.object_id)
                        if ci:
                            cache.incr(('content_import.matched.%s') % ci.pk)
                        print "MATCH!!! ", match
                    except:
                        if p['notes']:
                            desc = p['notes']
                        else:
                            desc = ""

                        if "tendenci" in p['name'].lower() or "t5" in p['name'].lower():
                            tech = "Tendenci"
                        elif "word" in p['name'].lower() or "wp" in p['name'].lower():
                            tech = "Wordpress"
                        elif "drupal" in p['name'].lower():
                            tech = "Drupal"
                        else:
                            tech = "Other"

                        if "sem" in p['name'].lower() or "seo" in p['name'].lower() or "ppc" in p['name'].lower() or "creative" in p['name'].lower():
                            ongoing = True
                        else:
                            ongoing = False

                        owner = Profile.objects.filter(user__is_active=True).order_by('?')[0].pk

                        if p['active']:
                            status = "In Progress"
                            end_dt = None
                        else:
                            status = "Done"
                            end_dt = p["updated_at"]

                        if p['cost_budget']:
                            budget = round(float(p['cost_budget']))/100
                        else:
                            budget = 100

                        try:
                            tp = ThirdParty.objects.get(
                                content_type=ContentType.objects.get(model='client'),
                                service_item_label='harvest_client_id',
                                service_item_value=p['client_id'],
                            )
                            client = Client.objects.get(id=tp.object_id)
                        except:
                            client = None

                        project = Project(
                            name=p['name'], 
                            description=desc,
                            technology=tech,
                            status=status,
                            ongoing=ongoing,
                            task_budget=budget,
                            owner_id=owner,
                            start_dt=p['created_at'],
                            end_dt=end_dt,
                            original_creator_id=1,
                            client=client,
                            editor_id=1)
                        project.save()
                        project.original = project
                        project.save()

                        obj, created = ThirdParty.objects.get_or_create(
                            content_type=ContentType.objects.get(model='project'),
                            object_id=project.id,
                            service_item_label='harvest_project_id',
                            service_item_value=p['id'],
                        )

                        obj, created = ThirdParty.objects.get_or_create(
                            content_type=ContentType.objects.get(model='project'),
                            object_id=project.id,
                            service_item_label='harvest_project_client_id',
                            service_item_value=p['client_id'],
                        )

                        if ci:
                            cache.incr(('content_import.added.%s') % ci.pk)
                        total += 1
            print "Done. Added %s of %s Projects" % (total, len(data))
        if ci:
            ci.complete_dt = timezone.now()
            cache.set(('content_import.complete_dt.%s') % ci.pk, ci.complete_dt)
            ci.matched = cache.get(('content_import.matched.%s') % ci.pk)
            ci.added = cache.get(('content_import.added.%s') % ci.pk)
            ci.estimated_total = cache.get(('content_import.total.%s') % ci.pk)
            ci.save()
