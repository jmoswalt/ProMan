from django.core.management.base import BaseCommand, CommandError

from proman.models import Client, Project
from proman.harvest import get_harvest_json

class Command(BaseCommand):
    """
    Loads in Projects from Harvest API
    """
    def handle(self, *args, **options):
        api_url = "/projects"
        total = 0
        json_data = get_harvest_json(api_url)
        if json_data:
            print "Connected"
            data = [a for a in json_data]
            for d in data:
                for p in d.itervalues():
                    if p['name'] != "Lost Time" and p['name'] != "Client Services":
                        try:
                            match = Project.objects.filter(harvest_project_id=p['id'])[0]
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
    
                            if p['active']:
                                status = "In Progress"
                            else:
                                status = "Done"
    
                            if p['cost_budget']:
                                budget = round(float(p['cost_budget']))/100
                            else:
                                budget = 100
    
                            try:
                                client = Client.objects.get(harvest_client_id=p['client_id'])
                            except:
                                client = None
    
                            project = Project(
                                harvest_project_id=p['id'], 
                                name=p['name'], 
                                description=desc,
                                technology=tech,
                                status=status,
                                ongoing=ongoing,
                                task_budget=budget,
                                owner_id=1,
                                start_dt=p['created_at'],
                                original_creator_id=1,
                                client=client,
                                editor_id=1)
                            project.save()
                            project.original = project
                            project.save()
                            total += 1
            print "Done. Added %s of %s Projects" % (total, len(data))
