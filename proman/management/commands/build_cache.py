from django.core.management.base import BaseCommand, CommandError

from proman.models import Profile, Project

class Command(BaseCommand):
    """
    Build our cache
    """
    def handle(self, *args, **options):
        apps = ['profiles']
        if args:
            apps = args

        # Loop through selected or default apps to cache
        for app in apps:
            if app == "profiles":
                print "Starting Profile Cache..."
                profiles = Profile.objects.all()
                for p in profiles:
                    p.client_name()
                    #p.get_absolute_url()
                    p.open_projects()
                    p.done_projects()
                    p.total_open_tasks()
                    p.velocity_tasks()
                    p.week_due_tasks()
                    p.week_done_tasks()
                print "Profile Cache Done."

            if app == "projects":
                print "Starting Project Cache..."
                projects = Project.objects.filter(version=False)
                for p in projects:
                    p.tasks_logs()
                    p.tasks()
                    p.tasks_done()
                    p.tasks_not_done()
                    p.harvest_project_id()
                    p.harvest_budget_spent()
                    p.owner_url()
                    p.owner_name()
                    p.client_name()
                    print p.pk
                print "Project Cache Done."