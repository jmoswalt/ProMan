from decimal import Decimal
from datetime import datetime, date, timedelta
from math import sqrt

from django.db import models
from django.db.models import Sum, Count
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from proman.utils import cache_item

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

HOURLY_RATE = 125
DEFAULT_RATE = 100
NOW_STR = datetime.strftime(timezone.now(), "%Y%m%d")

class Team(models.Model):
    name = models.CharField(max_length=100)
    leader = models.ForeignKey(User, related_name="team_leader", null=True)

    def __unicode__(self):
        return self.name

class Client(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

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
    client = models.ForeignKey(Client, null=True, related_name="project_client")

    # Versioning Info
    original_creator = models.ForeignKey(User, related_name="project_original_owner")
    editor = models.ForeignKey(User, related_name="project_editor")
    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)
    original = models.ForeignKey('self', null=True, related_name='project_original')
    version = models.BooleanField(default=False, db_index=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('project_detail', [self.pk])

    def age(self):
        today = timezone.now()
        if self.status == "Done":
            datediff = self.end_dt - self.start_dt
        else:
            datediff = today - self.start_dt
        if datediff.days > 0:
            return datediff.days
        return 0

    def tasks_logs(self):
        key = "project.tasks_logs"
        cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, self.id) 
        cached = cache.get(cache_key)
        if cached is None:
            task_pks = [item.pk for item in self.tasks()]
            cached = LogEntry.objects.filter(content_type=ContentType.objects.get(model='task'), action_flag__in=[1,5,6], object_id__in=task_pks).order_by('-action_time')[:6]
            if cached is None:
                cached = []
            cache_item(cached, cache_key)
        print cached
        return cached

    def tasks(self):
        key = "project.tasks"
        cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, self.id) 
        cached = cache.get(cache_key)
        if cached is None:
            cached = self.task_set.filter(version=False).order_by('due_dt')
            if cached is None:
                cached = []
            cache_item(cached, cache_key)
        return cached

    def tasks_count(self):
        if self.tasks():
            return self.tasks().count()
        return 0

    def tasks_hours(self):
        if self.tasks():
            return self.tasks().aggregate(total_time=Sum('task_time'))['total_time']
        return 0

    def tasks_done(self):
        key = "project.tasks_done"
        cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, self.id) 
        cached = cache.get(cache_key)
        if cached is None:
            cached = self.task_set.filter(version=False, completed=True).order_by('due_dt')
            if cached is None:
                cached = []
            cache_item(cached, cache_key)
        return cached

    def tasks_done_hours(self):
        if self.tasks_done():
            return self.tasks_done().aggregate(total_time=Sum('task_time'))['total_time']
        return 0

    def tasks_done_count(self):
        if self.tasks_done():
            return self.tasks_done().count()
        return 0

    def tasks_not_done(self):
        if self.tasks():
            undone = [t for t in self.tasks() if t not in self.tasks_done()]
            return undone
        return []

    def tasks_not_done_hours(self):
        if self.tasks_hours():
            return self.tasks_hours() - self.tasks_done_hours()
        return 0

    def tasks_not_done_count(self):
        if self.tasks_count():
            return self.tasks_count() - self.tasks_done_count()
        return 0

    def completion_perc(self):
        done = float(self.tasks_done_count())
        total = float(self.tasks_count())
        avg_tasks = 36.0
        lowest = done
        if done > avg_tasks: lowest = avg_tasks

        perc = 0
        if total > 0:
            # Custom formula from JMO and Alex
            perc = round((1 - ((total - done)/total))*(lowest/avg_tasks)*100, 1)

        return perc

    def score(self):
        # age * budget * 100 - completion percentage
        rate = self.age()*self.harvest_budget()["bp"]*(100 - self.completion_perc())*.001
        return int(round(sqrt(rate)))

    def budget_dollars(self):
        return self.task_budget*DEFAULT_RATE

    def perc_class(self):
        perc = self.completion_perc()
        pc = "info"
        if perc:
            if self.ongoing:
                pc = "info"
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

    def score_class(self):
        sc = "danger"
        if self.score() < 10:
            sc = "success"
        elif self.score() < 30:
            sc = "info"
        elif self.score() < 50:
            sc = "warning"

        return sc

    def status_class(self):
        if self.status == "Done":
            sc = "success"
        elif self.status == "Not Started":
            sc = "danger"
        else:
            sc = "warning"

        return sc

    def harvest_budget(self):
        hbs = self.harvest_budget_spent()
        if hbs > float(0) and self.budget_dollars() > float(0):
            bp = round((hbs/float(self.budget_dollars()))*100,1)
            if bp < 100:
                return {"first": bp,
                    "first_class": "success",
                    "bp": bp
                    }
            elif bp > 200:
                return {"first": 0,
                    "first_class": "success",
                    "over": bp - 100,
                    "over_perc": 100,
                    "neg_over": 100 - bp,
                    "over_class": "danger",
                    "bp": bp
                    }
            else:
                return {
                    "first": 200 - bp,
                    "first_class": "success",
                    "over": bp - 100,
                    "neg_over": 100 - bp,
                    "over_perc": bp - 100,
                    "over_class": "danger",
                    "bp": bp
                    }
        return {"bp": 0}

    def harvest_project_id(self):
        key = "project.harvest_project_id"
        cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, self.id) 
        cached = cache.get(cache_key)
        if cached is None:
            harvest_match = ThirdParty.objects.get(
                content_type=ContentType.objects.get(model='project'),
                object_id=self.id,
                service_item_label='harvest_project_id',
                )
            cached = harvest_match.service_item_value
            if cached is None:
                cached = []
            cache_item(cached, cache_key)
        return cached

    def harvest_budget_spent(self):
        hpi = self.harvest_project_id()
        if hpi:
            keys = [settings.SITE_CACHE_KEY, str('harvest_budget_spent'), str(self.id), NOW_STR]
            key = '.'.join(keys)
            if cache.get(key) is None:
                from proman.harvest import Harvest
                entries = Harvest().project_entries(
                    hpi,
                    datetime.strftime(self.start_dt, "%Y%m%d"),
                    NOW_STR,
                    "yes"
                    )
                hours = 0
                if entries:
                    for d in entries:
                        for e in d.itervalues():
                            hours = hours + float(e['hours'])
                value = int(round(hours*HOURLY_RATE))
                cache_item(value, key)
            return cache.get(key)
        return None

    def cached_owner_url(self):
        key = "profile.get_absolute_url"
        cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, self.owner_id) 
        cached = cache.get(cache_key)
        if cached is None:
            cached = self.owner.profile.get_absolute_url()
            cache_item(cached, cache_key)
        return cached

    def cached_owner_name(self):
        key = "profile.abbr_name"
        cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, self.owner_id) 
        cached = cache.get(cache_key)
        if cached is None:
            cached = self.owner.profile.abbr_name()
            cache_item(cached, cache_key)
        return cached

    def cached_client_name(self):
        key = "client.name"
        cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, self.client_id) 
        cached = cache.get(cache_key)
        if cached is None:
            if self.client:
                cached = self.client.name
            else:
                cached = None
            cache_item(cached, cache_key)
        return cached

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
    completed_dt = models.DateTimeField(_('Completion Date'), blank=True, null=True)
    task_time = models.DecimalField(_("Time"), max_digits=5, decimal_places=2, choices=TASK_TIME_CHOICES, default='1.00')
    completed = models.BooleanField(default=False)
    private = models.BooleanField(default=False)
    stuck = models.BooleanField(default=False)
    #TODO: Change this to pull from the API. Probably a new model and M2M on it
    billable = models.BooleanField(default=True)
    resolution = models.TextField(blank=True)

    # Versioning Info
    original_creator = models.ForeignKey(User, related_name="task_original_owner")
    editor = models.ForeignKey(User, related_name="task_version_owner")
    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)
    original = models.ForeignKey('self', related_name='task_original', null=True)
    version = models.BooleanField(default=False, db_index=True)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('task_detail', [self.pk])

    def overdue(self):
        if self.due_dt and not self.completed:
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

    def cached_assignee_url(self):
        key = "profile.get_absolute_url"
        cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, self.assignee_id) 
        cached = cache.get(cache_key)
        if cached is None:
            cached = self.assignee.profile.get_absolute_url()
            cache_item(cached, cache_key)
        return cached

    def cached_assignee_name(self):
        key = "profile.abbr_name"
        cache_key = "%s.%s.%s" % (settings.SITE_CACHE_KEY, key, self.assignee_id) 
        cached = cache.get(cache_key)
        if cached is None:
            cached = self.assignee.profile.abbr_name()
            cache_item(cached, cache_key)
        return cached


MONDAY = datetime.now() - timedelta(days=datetime.now().weekday())
SUNDAY = datetime.now() + timedelta(days=(6 - datetime.now().weekday()))

PROFILE_ROLE_CHOICES = (
    ('employee','Employee'),
    ('client','Client'),
)

class Profile(models.Model):
    """
    Profile for users to add more fields.
    """
    user = models.OneToOneField(User)
    role = models.CharField(choices=PROFILE_ROLE_CHOICES, max_length=20, default='client') 
    team = models.ForeignKey(Team, related_name="team", null=True)

    @models.permalink
    def get_absolute_url(self):
        return ('user_detail', [self.user.username])

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
        tasks = Task.objects.filter(version=False, assignee=self.user).exclude(completed=True).aggregate(total_hours=Sum('task_time'), num_tasks=Count('pk'))
        return tasks

    def velocity_tasks(self):
        today = SUNDAY - timedelta(weeks=1)
        three_weeks_ago = MONDAY - timedelta(weeks=4)
        tasks = Task.objects.filter(version=False, assignee=self.user, completed=True, due_dt__gte=three_weeks_ago, due_dt__lte=today).aggregate(total_hours=Sum('task_time'), num_tasks=Count('pk'))
        if tasks['total_hours'] > 0:
            tasks['total_hours'] = round(tasks['total_hours']/3,2)
        if tasks['num_tasks'] > 0:
            tasks['num_tasks'] = round(Decimal(tasks['num_tasks'])/3,2)
        return tasks

    def week_due_tasks(self):
        tasks = Task.objects.filter(version=False, assignee=self.user, due_dt__gte=MONDAY, due_dt__lte=SUNDAY).exclude(completed=True).aggregate(total_hours=Sum('task_time'), num_tasks=Count('pk'))
        return tasks

    def week_done_tasks(self):
        tasks = Task.objects.filter(version=False, assignee=self.user, completed=True, completed_dt__gte=MONDAY, completed_dt__lte=SUNDAY).aggregate(total_hours=Sum('task_time'), num_tasks=Count('pk'))
        return tasks

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def update_active_user_cache(sender, instance, created, **kwargs):
    key = ".".join([settings.SITE_CACHE_KEY,'active_users'])
    value = Profile.objects.filter(user__is_active=True).order_by('user__last_name').select_related()
    cache.set(key, value)

post_save.connect(create_user_profile, sender=User)
post_save.connect(update_active_user_cache, sender=Profile)

class ThirdParty(models.Model):
    content_type = models.ForeignKey(ContentType, db_index=True)
    object_id = models.PositiveIntegerField()
    service_item_label = models.CharField(max_length=100)
    service_item_value = models.CharField(max_length=500)
