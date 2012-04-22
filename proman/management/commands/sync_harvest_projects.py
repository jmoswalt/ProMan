from django.core.management.base import BaseCommand, CommandError
from proman.models import Project

class Command(BaseCommand):
    """
    Clears the entire site cache
    """
    def handle(self, *args, **options):
        from django.conf import settings
        from harvest import Harvest
        print "Trying to connect... "
        try:
            h_conn = Harvest(settings.HV_URL, settings.HV_USER, settings.HV_PASS)
        except:
            h_conn = None
        if not h_conn:
            print "Missing or invalid settings to connect"
        else:
            print "Got connected"
            for p in h_conn.projects():
                if p.name != "Lost Time" and p.name != "Client Services":
                    try:
                        match = Project.objects.filter(harvest=p.id)[0]
                        print "MATCH!!! ", match
                    except:
                        if p.notes:
                            desc = p.notes
                        else:
                            desc = ""

                        if "tendenci" in p.name.lower() or "t5" in p.name.lower():
                            tech = "Tendenci"
                        elif "word" in p.name.lower() or "wp" in p.name.lower():
                            tech = "Wordpress"
                        elif "drupal" in p.name.lower():
                            tech = "Drupal"
                        else:
                            tech = "Other"

                        if "sem" in p.name.lower() or "seo" in p.name.lower() or "ppc" in p.name.lower() or "creative" in p.name.lower():
                            ongoing = True
                        else:
                            ongoing = False

                        if p.active:
                            status = "In Progress"
                        else:
                            status = "Done"

                        if p.cost_budget:
                            budget = p.cost_budget/100
                        else:
                            budget = 100

                        project = Project(
                            harvest=p.id, 
                            name=p.name, 
                            description=desc,
                            technology=tech,
                            status=status,
                            ongoing=ongoing,
                            task_budget=budget,
                            owner_id=1,
                            start_dt=p.created_at,
                            original_creator_id=1,
                            editor_id=1)
                        project.save()