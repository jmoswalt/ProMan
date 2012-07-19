from django.core.management.base import BaseCommand, CommandError

from pm.models import Profile, Project, Task

class Command(BaseCommand):
    """
    Build our cache
    """
    def handle(self, *args, **options):
        apps = ['profiles', 'projects', 'tasks']
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
                    p.projects()
                    p.tasks()
                print "Profile Cache Done."

            if app == "projects":
                print "Starting Project Cache..."
                projects = Project.originals.all()
                for p in projects:
                    #p.tasks_logs()
                    p.tasks()
                    p.harvest_project_id()
                    p.harvest_budget_spent()
                    p.owner_url()
                    p.owner_name()
                    p.client_name()
                    print p.pk
                print "Project Cache Done."

            if app == "tasks":
                print "Starting Task Cache..."
                tasks = Task.originals.all()
                for t in tasks:
                    t.project_name()
                print "Task Cache Done."
