from datetime import date, datetime, timedelta
import subprocess

from django.conf import settings
from django.db.models import Q, Sum, Avg, Count
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import Http404
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.views.generic.edit import FormMixin, ModelFormMixin
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.core.cache import cache
from django.core.management import call_command
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.mail import send_mail

from proman.models import Project, Task, Profile, ContentImport
from proman.forms import TaskForm, TaskMiniForm, TaskCloseForm, ProjectForm, ProfileForm
from proman.utils import get_task_change_message, get_project_change_message, get_profile_change_message

START_DT_INITIAL = timezone.now()
END_DT_INITIAL = timezone.now() + timedelta(days=90)
DUE_DT_INITIAL = timezone.now() + timedelta(weeks=1)

#Custom Action Flags
CLOSED = 5
MISSED = 6


def UserCurrent(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('user_detail', args=[request.user.username]))
    return HttpResponseRedirect(reverse('home'))


def UserIdRedirect(request, pk=None):
    user = get_object_or_404(User, pk=pk)
    return HttpResponseRedirect(reverse('user_detail', args=[user.username]))


class UserListView(ListView):
    model = Profile
    template_name = "proman/user_list.html"

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(UserListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['inactive_employees'] = Profile.objects.inactive_employees()
        context['active_employees'] = Profile.objects.active_employees()
        inactive_employees = context['inactive_employees']
        inactive_pks = [p.pk for p in inactive_employees]
        context['open_projects_inactives'] = Project.objects.filter(version=False, owner_id__in=inactive_pks).exclude(status="done")
        context['open_tasks_inactives'] = Task.objects.filter(version=False, owner_id__in=inactive_pks, completed=False)
        return context

class ContactListView(UserListView):
    queryset = Profile.objects.filter(user__is_staff=False).order_by('last_name')
    context_object_name = "profiles"
    template_name = "proman/client_list.html"


class UserCreateView(CreateView):
    """
    Creates a Profile
    """
    form_class = ProfileForm
    template_name = "proman/user_update.html"

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(UserCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        username = self.object.email
        if form.cleaned_data['username']:
            username = form.cleaned_data['username']
        user_object = User.objects.create(username=username, email=self.object.email, first_name=self.object.first_name, last_name=self.object.last_name, is_active=True)
        self.object.user = user_object
        self.object.save()

        change_message = "added this profile"

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object), 
            action_flag     = ADDITION,
            change_message  = change_message
        )

        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        if self.request.GET.has_key('next'):
            messages.success(self.request, 'Successfully added the profile for <strong><a href="%s">%s</a></strong>.' % (self.object.get_absolute_url(), self.object.nice_name()), extra_tags='success profile-%s' % self.object.pk)
            return self.request.GET['next']

        messages.success(self.request, 'Successfully added this profile.', extra_tags='success profile-%s' % self.object.pk)
        return self.object.get_absolute_url()


class UserUpdateView(UpdateView):
    """
    Updates a Profile
    """
    form_class = ProfileForm
    template_name = "proman/user_update.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserUpdateView, self).dispatch(*args, **kwargs)

    def get_object(self, **kwargs):
        obj = get_object_or_404(Profile, pk=self.kwargs['pk'])
        return obj

    def get_initial(self):
        super(UserUpdateView, self).get_initial()
        if self.get_object().user.is_staff:
            role = "1"
        else:
            role = "0"

        self.initial = {
            "username": self.get_object().user.username,
            "role": role,
            "active": self.get_object().user.is_active,
        }
        return self.initial

    def form_valid(self, form):
        self.object = form.save(commit=False)
        orig = Profile.objects.get(pk=self.object.pk)
        self.object = form.save()
        profile = self.object
        profile.user.first_name = profile.first_name
        profile.user.last_name = profile.last_name
        profile.user.email = profile.email
        profile.user.username = form.cleaned_data['username']

        if form.cleaned_data['role'] == "1":
            profile.user.is_staff = True
        else:
            profile.user.is_staff = False

        profile.user.is_active = form.cleaned_data['active']
        profile.user.save()

        change_message = get_profile_change_message(orig, self.object)

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object), 
            action_flag     = CHANGE,
            change_message  = change_message
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.request.GET.has_key('next'):
            messages.success(self.request, 'Successfully updated the profile for <strong><a href="%s">%s</a></strong>.' % (self.object.get_absolute_url(), self.object.nice_name()), extra_tags='success profile-%s' % self.object.pk)
            return self.request.GET['next']

        messages.success(self.request, 'Successfully updated this profile.', extra_tags='success profile-%s' % self.object.pk)
        return self.object.get_absolute_url()


class UserDetailView(DetailView):
    model = Profile
    context_object_name = "profile"
    template_name = "proman/profile_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        #TODO: Move all of these contexts into methods for the Profile 

        # Pull projects for a client
        if context['profile'].client:
            context['user_projects'] = Project.objects.filter(version=False, client=context['profile'].client).order_by('-status', 'start_dt')
            context['user_open_project_tasks'] = Task.objects.filter(version=False, project__client=context['profile'].client).exclude(completed=True, private=True).order_by('due_dt')

        context['results_paginate'] = "10"
        return context

    def get_object(self, **kwargs):
        obj = get_object_or_404(Profile, user__username=self.kwargs['username'])
        return obj

    def render_to_response(self, context):
        """Used to pull paginated items via a GET"""
        if self.request.method == 'GET':
            if self.request.GET.get('open_task_page'):
                open_task_page = self.request.GET.get('open_task_page')
                paginator = Paginator(context['user_open_project_tasks'], context['results_paginate'])
                task_items = paginator.page(open_task_page).object_list
                return render_to_response("proman/task_table_items.html", locals(), context_instance=RequestContext(self.request))

            if self.request.GET.get('done_task_page'):
                done_task_page = self.request.GET.get('done_task_page')
                paginator = Paginator(context['user_done_project_tasks'], context['results_paginate'])
                task_items = paginator.page(done_task_page).object_list
                return render_to_response("proman/task_table_items.html", locals(), context_instance=RequestContext(self.request))

            if self.request.GET.get('done_task_search'):
                done_task_count = self.request.GET.get('done_task_search')
                task_items = context['user_done_project_tasks'][done_task_count:]
                return render_to_response("proman/task_table_items.html", locals(), context_instance=RequestContext(self.request))

            if self.request.GET.get('open_task_search'):
                open_task_count = self.request.GET.get('open_task_search')
                task_items = context['user_open_project_tasks'][open_task_count:]
                return render_to_response("proman/task_table_items.html", locals(), context_instance=RequestContext(self.request))

        return render_to_response(self.template_name, context, context_instance=RequestContext(self.request))

class TaskCreateView(CreateView):
    """
    Creates a Task
    """
    form_class = TaskForm
    template_name = "proman/task_update.html"
    success_url = '/projects/'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TaskCreateView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        super(TaskCreateView, self).get_initial()
        project = self.request.GET.get("project")
        user = self.request.user
        self.initial = {"owner":user.id, "project":project, "due_dt": DUE_DT_INITIAL}
        return self.initial
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.original_creator = self.request.user.profile
        self.object.editor = self.request.user.profile
        self.object.save()
        self.object.original = self.object
        self.object.save()

        change_message = "added this task"

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object), 
            action_flag     = ADDITION,
            change_message  = change_message
        )

        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        if self.request.GET.has_key('next'):
            messages.success(self.request, 'Successfully added the task <strong><a href="%s">%s</a></strong>.' % (self.object.get_absolute_url(), self.object.title), extra_tags='success task-%s' % self.object.pk)
            return self.request.GET['next']
        
        messages.success(self.request, 'Successfully added the task <strong>%s</strong>.' % self.object.title, extra_tags='success task-%s' % self.object.pk)
        return HttpResponseRedirect(reverse('project_detail', args=[self.object.project.pk]))


class TaskUpdateView(UpdateView):
    """
    Updates a Task
    """
    form_class = TaskForm
    template_name = "proman/task_update.html"
    success_url = '/projects/'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TaskUpdateView, self).dispatch(*args, **kwargs)

    def get_object(self, **kwargs):
        obj = get_object_or_404(Task, pk=self.kwargs['pk'])
        return obj

    def form_valid(self, form):
        self.object = form.save(commit=False)
        orig = Task.objects.get(pk=self.object.pk)
        new_obj = orig
        new_obj.pk = None
        new_obj.editor = self.request.user.profile
        new_obj.version = True
        new_obj.save()
        self.object.save()

        action_flag = CHANGE
        change_message = get_task_change_message(orig, self.object)

        # if changed from not done to done
        if not orig.completed and self.object.completed:
            action_flag = CLOSED

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object), 
            action_flag     = action_flag,
            change_message  = change_message
        )
#         if self.request.user != self.object.owner and new_obj.owner != self.object.owner:
#             # If you aren't changing to yourself, and the owner changed, send them an email.
#             send_mail('[PM] Task Assigned %s' % self.object.title, "You've just been assigned the following task from %s: <br />%s (Link: %s%s)<br /><br /> %s<br /><br />" % (self.request.user.username, self.object.title, settings.SITE_URL, self.object.get_absolute_url(), self.object.description), self.request.user.email, [self.object.owner.email], fail_silently=False)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.request.GET.has_key('next'):
            messages.success(self.request, 'Successfully updated the task <strong><a href="%s">%s</a></strong>.' % (self.object.get_absolute_url(), self.object.title), extra_tags='success task-%s' % self.object.pk)
            return self.request.GET['next']
        
        messages.success(self.request, 'Successfully updated this task.', extra_tags='success task-%s' % self.object.pk)
        return self.object.get_absolute_url()

class TaskCloseUpdateView(TaskUpdateView):
    """
    Mini Form to Close a Task
    """
    form_class = TaskCloseForm

    def get_success_url(self):
        if self.request.GET.has_key('next'):
            messages.success(self.request, 'Successfully closed the task <strong><a href="%s">%s</a></strong>.' % (self.object.get_absolute_url(), self.object.title), extra_tags='success task-%s' % self.object.pk)
            return self.request.GET['next']
        
        messages.success(self.request, 'Successfully closed this task.', extra_tags='success task-%s' % self.object.pk)
        return self.object.get_absolute_url()

class TaskDetailView(DetailView):
    model = Task
    template_name = "proman/task_detail.html"
    context_object_name = "task"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TaskDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        form = TaskCloseForm(instance=self.object)
        form.initial = {"completed_dt": START_DT_INITIAL}

        context = super(TaskDetailView, self).get_context_data(**kwargs)
        context['close_form'] = form
        context['task_logs'] = LogEntry.objects.filter(object_id=self.object.pk, content_type = ContentType.objects.get_for_model(self.object).pk).order_by('-action_time')
        return context


class ProjectCreateView(CreateView):
    """
    Creates a Project
    """
    form_class = ProjectForm
    template_name = "proman/project_update.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectCreateView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        super(ProjectCreateView, self).get_initial()
        user = self.request.user
        self.initial = {"owner":user.id, "start_dt": START_DT_INITIAL, "end_dt": END_DT_INITIAL}
        return self.initial
    
    def form_valid(self, form):
        self.object = form.save(commit=False)

        change_message = "added this project"

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object), 
            action_flag     = ADDITION,
            change_message  = change_message
        )

        messages.success(self.request, "Successfully added this new project, <strong>%s</strong>." % self.object.name, extra_tags='success')

        return HttpResponseRedirect(reverse('project_detail', args=[self.object.pk]))

    def get_success_url(self):
        if self.request.GET.has_key('next'):
            return self.request.GET['next']
        return self.object.get_absolute_url()

class ProjectUpdateView(UpdateView):
    """
    Updates a Project
    """
    form_class = ProjectForm
    template_name = "proman/project_update.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectUpdateView, self).dispatch(*args, **kwargs)

    def get_object(self, **kwargs):
        obj = get_object_or_404(Project, pk=self.kwargs['pk'])
        return obj

    def form_valid(self, form):
        self.object = form.save(commit=False)
        orig = Project.objects.get(pk=self.object.pk)
        new_obj = orig
        new_obj.pk = None
        new_obj.editor = self.request.user.profile
        new_obj.version = True
        new_obj.save()
        self.object.save()

        change_message = get_project_change_message(orig, self.object)

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object), 
            action_flag     = CHANGE,
            change_message  = change_message
        )

        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        if self.request.GET.has_key('next'):
            messages.success(self.request, 'Successfully updated the project <strong><a href="%s">%s</a></strong>.' % (self.object.get_absolute_url(), self.object.name), extra_tags='success project-%s' % self.object.pk)
            return self.request.GET['next']
        
        messages.success(self.request, 'Successfully updated this project.', extra_tags='success project-%s' % self.object.pk)
        return self.object.get_absolute_url()


class ProjectListView(ListView):
    model = Project
    queryset = Project.objects.filter(version=False).exclude(status="Done").order_by('-status', 'start_dt')[:25]
    context_object_name = "projects"
    template_name = "proman/project_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)

        projects = Project.objects.filter(version=False).exclude(status="Done").order_by('-status', 'start_dt')
        context['display'] = "open"
        if self.request.GET.get('display'):
            display = self.request.GET.get('display')
            if display == "all":
                context['display'] = display
                projects = Project.objects.filter(version=False).order_by('-status', 'start_dt')
            if display == "done":
                context['display'] = display
                projects = Project.objects.filter(version=False, status="Done").order_by('-status', 'start_dt')
        context['filtered_projects'] = projects
        context['projects_total'] = projects.count()
        context['results_paginate'] = "25"
        context['projects'] = projects[:context['results_paginate']]
        return context

    def render_to_response(self, context):
        """Used to pull paginated items via a GET"""
        if self.request.method == 'GET':
            if self.request.GET.get('project_page'):
                project_page = self.request.GET.get('project_page')
                paginator = Paginator(context['filtered_projects'], context['results_paginate'])
                projects = paginator.page(project_page).object_list
                return render_to_response("proman/project_table_items.html", locals(), context_instance=RequestContext(self.request))

            if self.request.GET.get('project_search'):
                project_count = self.request.GET.get('project_search')
                current_count = self.request.GET.get('project_current')
                projects = context['filtered_projects'][project_count:]
                return render_to_response("proman/project_table_items.html", locals(), context_instance=RequestContext(self.request))

        return render_to_response(self.template_name, context, context_instance=RequestContext(self.request))

class ProjectDetailView(DetailView):
    model = Project
    template_name = "proman/project_detail.html"
    context_object_name = "project"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectDetailView, self).dispatch(*args, **kwargs)


    def get_context_data(self, **kwargs):
        project = self.object.pk
        user = self.request.user
        form = TaskMiniForm()
        form.fields['owner'].initial = user.profile.id
        form.fields['project'].initial = project
        form.fields['due_dt'].initial = DUE_DT_INITIAL
        form.fields['billable'].initial = True
        context = super(ProjectDetailView, self).get_context_data(**kwargs)

        project_tasks = Task.objects.filter(version=False, project=self.kwargs['pk'])

        context['form'] = form
        context['project_logs'] = LogEntry.objects.filter(object_id=self.object.pk, content_type = ContentType.objects.get_for_model(self.object).pk).order_by('-action_time')

        return context


@login_required
def import_content(request, content_type=None, template_name="proman/import.html"):
    if content_type not in ['clients', 'projects', 'users', 'client_contacts']:
        raise Http404
    ci = ContentImport.objects.create(content_type=content_type, starter=request.user.profile)
    return HttpResponseRedirect(reverse('import_content_attempt', kwargs={'content_type': content_type, 'pk': int(ci.pk)}))


@login_required
def import_content_attempt(request, content_type=None, pk=None, template_name="proman/import.html"):
    if content_type not in ['clients', 'projects', 'users', 'client_contacts']:
        raise Http404
    ci = get_object_or_404(ContentImport, pk=pk)
    if not ci.create_dt:
        ci.create_dt = timezone.now()
        ci.save()
        command = 'import_harvest_%s' % ci.content_type
        subprocess.Popen(["python", "manage.py", command, str(ci.pk)])
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


@login_required
def import_check(request, pk=None, template_name="proman/import_check.html"):
    """
    Check the import record for matched, added, total, and completeness.
    Also create the percentage for the bar graph. Render all of these in a hidden
    div in a template to be reformatted and displayed by javascript
    """
    if pk:
        matched = cache.get(('content_import.matched.%s') % pk)
        added = cache.get(('content_import.added.%s') % pk)
        total = cache.get(('content_import.total.%s') % pk)
        complete_dt = cache.get(('content_import.complete_dt.%s') % pk)
        perc = 0
        if total > 0:
            perc = int(round((matched + added)*100/total))
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))
