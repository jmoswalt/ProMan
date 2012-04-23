from decimal import Decimal
from datetime import datetime, date, timedelta

from django.db import models
from django.db.models import Sum, Count
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

PROJECT_TECHNOLOGY_CHOICES = (
    ('Tendenci','Tendenci'),
    ('WordPress','WordPress'),
    ('Drupal','Drupal'),
    ('Other','Other'),
)

PROJECT_STATUS_CHOICES = (
    ('Not Started','Not Started'),
    ('In Progress','In Progress'),
    ('Done','Done'),
)

class Client(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    harvest_client_id = models.IntegerField(blank=True, default=0)

class Project(models.Model):
    """
    A project is a collection of tasks with a start and end date
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, related_name="project_owner")
    start_dt = models.DateTimeField(_('Start Date'))
    end_dt = models.DateTimeField(_('End Date'), blank=True, null=True)
    task_budget = models.IntegerField(blank=True, default=80)
    technology = models.CharField(choices=PROJECT_TECHNOLOGY_CHOICES, max_length=50, default='tendenci')
    status = models.CharField(choices=PROJECT_STATUS_CHOICES, max_length=20, default='unstarted')
    ongoing = models.BooleanField(default=False)
    harvest_project_id = models.IntegerField(blank=True, default=0)
    client = models.ForeignKey(Client, null=True, related_name="project_client")

    # Versioning Info
    original_creator = models.ForeignKey(User, related_name="project_original_owner")
    editor = models.ForeignKey(User, related_name="project_editor")
    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)
    original = models.ForeignKey('self', null=True, related_name='project_original')
    version = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('project_detail', [self.pk])

    def age(self):
        today = timezone.now()
        datediff = today - self.start_dt
        if datediff.days > 0:
            return datediff.days
        return 0

    def task_count(self):
        tasks = self.task_set.filter(version=False).count()
        return tasks

    def task_done_count(self):
        tasks = self.task_set.filter(version=False, status="done").count()
        return tasks

    def task_hours(self):
        tasks = self.task_set.filter(version=False).aggregate(total_time=Sum('task_time'))
        return tasks['total_time']

    def task_done_hours(self):
        tasks = self.task_set.filter(version=False, status="done").aggregate(total_time=Sum('task_time'))
        return tasks['total_time']

    def completion_perc(self):
        perc = 0
        done_tasks = self.task_set.filter(version=False, status="done").aggregate(total_time=Sum('task_time'))

        if self.task_budget > 0:
            perc = round((done_tasks['total_time'] / self.task_budget)*100, 1)

        return perc

    def perc_class(self):
        perc = self.completion_perc()
        pc = "info"
        if perc:
            if self.ongoing:
                pc = "info"
            elif perc < 10:
                pc = "danger"
            elif perc >= 90:
                pc = "success"
        return pc

    def age_class(self):
        ac = "danger"
        if self.ongoing:
            ac = "info"
        elif self.age() < 40:
            ac = "success"
        elif self.age() < 70:
            ac = "info"
        elif self.age() < 90:
            ac = "warning"

        return ac

    def status_class(self):
        if self.status == "Done":
            sc = "success"
        elif self.status == "Not Started":
            sc = "danger"
        else:
            sc = "warning"
        return sc

TASK_TIME_CHOICES = (
    (Decimal('0.25'),'15 Mins'),
    (Decimal('0.50'),'30 Mins'),
    (Decimal('1.00'),'1 Hour'),
    (Decimal('1.50'),'1.5 Hours'),
    (Decimal('2.00'),'2 Hours'),
    (Decimal('3.00'),'3 Hours'),
    (Decimal('5.00'),'5 Hours'),
    (Decimal('8.00'),'8 Hours'),
)

TASK_STATUS_CHOICES = (
    ('Not Started','Not Started'),
    ('In Progress','In Progress'),
    ('Done', 'Done'),
    ('Stuck','Stuck'),
)

class Task(models.Model):
    """
    A task is an activity to be completed to help complete a project
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project)
    assignee = models.ForeignKey(User, related_name="assignee", verbose_name="Assign to")
    due_dt = models.DateTimeField(_('Due Date'), blank=True, null=True)
    task_time = models.DecimalField(_("Time"), max_digits=5, decimal_places=2, choices=TASK_TIME_CHOICES, default='0.50')
    status = models.CharField(choices=TASK_STATUS_CHOICES, max_length=20, default='unstarted')
    private = models.BooleanField(default=False)
    billable = models.BooleanField(default=True)
    resolution = models.TextField(blank=True)

    # Versioning Info
    original_creator = models.ForeignKey(User, related_name="task_original_owner")
    editor = models.ForeignKey(User, related_name="task_version_owner")
    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)
    original = models.ForeignKey('self', related_name='task_original', null=True)
    version = models.BooleanField(default=False)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('task_detail', [self.pk])

    def overdue(self):
        if self.due_dt and self.status != "Done":
            today = timezone.now()
            datediff = self.due_dt - today
            if datediff.days < 0:
                return True
        return False

    def due_age(self):
        if self.due_dt:
            today = timezone.now()
            datediff = self.due_dt - today
            return datediff.days
        return None

    def due_class(self):
        dc = None
        if self.due_age():
            if self.due_age() < 1:
                dc = "danger"
            elif self.due_age() <=1:
                dc = "warning"

        return dc


MONDAY = datetime.now() - timedelta(days=datetime.now().weekday())
SUNDAY = datetime.now() + timedelta(days=(6 - datetime.now().weekday()))

PROFILE_ROLE_CHOICES = (
    ('Employee','Employee'),
    ('Client','Client'),
)

class Profile(models.Model):
    """
    Profile for users to add more fields.
    """
    user = models.OneToOneField(User)
    role = models.CharField(choices=PROFILE_ROLE_CHOICES, max_length=20, default='client') 

    def nice_name(self):
        if self.user.first_name or self.user.last_name:
            return "%s %s" % (self.user.first_name, self.user.last_name)
        return self.user.username

    def abbr_name(self):
        if self.user.first_name or self.user.last_name:
            return "%s %s." % (self.user.first_name, self.user.last_name[:1])
        return self.user.username

    def open_projects(self):
        projects = Project.objects.filter(version=False, owner=self.user).exclude(status="done").count()
        return projects

    def total_open_tasks(self):
        tasks = Task.objects.filter(version=False, assignee=self.user).exclude(status="done").aggregate(total_hours=Sum('task_time'), num_tasks=Count('pk'))
        return tasks

    def velocity_tasks(self):
        today = SUNDAY - timedelta(weeks=1)
        three_weeks_ago = MONDAY - timedelta(weeks=4)
        tasks = Task.objects.filter(version=False, assignee=self.user, status="done", due_dt__gte=three_weeks_ago, due_dt__lte=today).aggregate(total_hours=Sum('task_time'), num_tasks=Count('pk'))
        if tasks['total_hours'] > 0:
            tasks['total_hours'] = round(tasks['total_hours']/3,2)
        if tasks['num_tasks'] > 0:
            tasks['num_tasks'] = round(Decimal(tasks['num_tasks'])/3,2)
        return tasks

    def week_due_tasks(self):
        tasks = Task.objects.filter(version=False, assignee=self.user, due_dt__gte=MONDAY, due_dt__lte=SUNDAY).exclude(status="done").aggregate(total_hours=Sum('task_time'), num_tasks=Count('pk'))
        return tasks

    def week_done_tasks(self):
        tasks = Task.objects.filter(version=False, assignee=self.user, status="done", due_dt__gte=MONDAY, due_dt__lte=SUNDAY).aggregate(total_hours=Sum('task_time'), num_tasks=Count('pk'))
        return tasks

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
