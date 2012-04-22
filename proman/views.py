from datetime import date, datetime, timedelta

from django.conf import settings
from django.db.models import Q, Sum, Avg, Count
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.views.generic.edit import FormMixin, ModelFormMixin
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.core.mail import send_mail

from proman.models import Project, Task, UserMethods
from proman.forms import TaskForm, TaskMiniForm, TaskCloseForm, ProjectForm
from proman.utils import get_task_change_message

START_DT_INITIAL = datetime.now()
END_DT_INITIAL = datetime.now() + timedelta(days=90)
DUE_DT_INITIAL = datetime.now() + timedelta(weeks=1)


class UserListView(ListView):
    model = User
    queryset = UserMethods.objects.filter(is_active=True)
    context_object_name = "users"
    template_name = "proman/user_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserListView, self).dispatch(*args, **kwargs)

class UserDetailView(DetailView):
    model = UserMethods
    context_object_name = "user_object"
    template_name = "proman/user_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        context['user_open_project_tasks'] = Task.objects.filter(version=False, assignee__username=self.kwargs['username']).exclude(status="done").order_by('due_dt','-status')
        context['user_done_project_tasks'] = Task.objects.filter(version=False, assignee__username=self.kwargs['username'], status="done").order_by('due_dt','-status')

        context['user_project_tasks_hours'] = context['user_open_project_tasks'].aggregate(total=Sum('task_time'))
        
        context['project_tasks_stuck'] = Task.objects.filter(version=False, assignee__username=self.kwargs['username'], status="stuck").annotate(hours=Sum('task_time')).order_by('due_dt')
        context['project_tasks_stuck_hours'] = context['project_tasks_stuck'].aggregate(total=Sum('task_time'))

        context['project_tasks_in_progress'] = Task.objects.filter(version=False, assignee__username=self.kwargs['username'], status="in progress").annotate(hours=Sum('task_time')).order_by('due_dt')
        context['project_tasks_in_progress_hours'] = context['project_tasks_in_progress'].aggregate(total=Sum('task_time'))

        context['project_tasks_not_started'] = Task.objects.filter(version=False, assignee__username=self.kwargs['username'], status="not started").order_by('due_dt')
        context['project_tasks_not_started_hours'] = context['project_tasks_not_started'].aggregate(total=Sum('task_time'))

        context['project_tasks_done'] = Task.objects.filter(version=False, assignee__username=self.kwargs['username'], status="done").order_by('due_dt')
        context['project_tasks_done_hours'] = context['project_tasks_done'].aggregate(total=Sum('task_time'))
        
        context['user_projects'] = Project.objects.filter(version=False, owner__username=self.kwargs['username']).order_by('status', 'start_dt')
        context['user_open_projects'] = Project.objects.filter(version=False, owner__username=self.kwargs['username']).exclude(status="done")
        context['user_open_project_stats'] = Project.objects.filter(version=False, owner__username=self.kwargs['username']).exclude(status="done").aggregate(total_tasks=Count('task'), total_task_hours=Sum('task__task_time'))

        context['results_paginate'] = "10"
        return context

    def get_object(self, **kwargs):
        obj = get_object_or_404(UserMethods, username=self.kwargs['username'])
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
    template_name = "proman/task_create.html"
    success_url = '/projects/'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TaskCreateView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        super(TaskCreateView, self).get_initial()
        project = self.request.GET.get("project")
        user = self.request.user
        self.initial = {"assignee":user.id, "project":project, "due_dt": DUE_DT_INITIAL}
        return self.initial
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.original_creator = self.request.user
        self.object.editor = self.request.user
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
        new_obj.editor = self.request.user
        new_obj.version = True
        new_obj.save()
        self.object.save()

        change_message = get_task_change_message(orig, self.object)

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object), 
            action_flag     = CHANGE,
            change_message  = change_message
        )
#         if self.request.user != self.object.assignee and new_obj.assignee != self.object.assignee:
#             # If you aren't changing to yourself, and the assignee changed, send them an email.
#             send_mail('[PM] Task Assigned %s' % self.object.title, "You've just been assigned the following task from %s: <br />%s (Link: %s%s)<br /><br /> %s<br /><br />" % (self.request.user.username, self.object.title, settings.SITE_URL, self.object.get_absolute_url(), self.object.description), self.request.user.email, [self.object.assignee.email], fail_silently=False)

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
        task = self.object
        task.status = "Done"
        form = TaskCloseForm(instance=task)

        context = super(TaskDetailView, self).get_context_data(**kwargs)
        context['close_form'] = form
        context['task_logs'] = LogEntry.objects.filter(object_id=self.object.pk, content_type = ContentType.objects.get_for_model(self.object).pk).order_by('-action_time')
        return context


class ProjectCreateView(CreateView):
    """
    Creates a Project
    """
    form_class = ProjectForm
    template_name = "proman/project_create.html"

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
        self.object.original_creator = self.request.user
        self.object.editor = self.request.user
        self.object.save()
        self.object.original = self.object
        self.object.save()

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object), 
            action_flag     = ADDITION
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
        new_obj.editor = self.request.user
        new_obj.version = True
        new_obj.save()
        self.object.save()

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object), 
            action_flag     = CHANGE
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
    queryset = Project.objects.filter(version=False)
    context_object_name = "projects"
    template_name = "proman/project_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        context['projects'] = Project.objects.filter(version=False).order_by('-status', 'start_dt')
        context['results_paginate'] = "3"
        return context

    def render_to_response(self, context):
        """Used to pull paginated items via a GET"""
        if self.request.method == 'GET':
            if self.request.GET.get('project_page'):
                project_page = self.request.GET.get('project_page')
                print project_page
                paginator = Paginator(context['projects'], context['results_paginate'])
                projects = paginator.page(project_page).object_list
                return render_to_response("proman/project_table_items.html", locals(), context_instance=RequestContext(self.request))

            if self.request.GET.get('project_search'):
                project_count = self.request.GET.get('project_search')
                projects = context['projects'][project_count:]
                print projects
                return render_to_response("proman/project_table_items.html", locals(), context_instance=RequestContext(self.request))

        return render_to_response(self.template_name, context, context_instance=RequestContext(self.request))

class ProjectDetailView(DetailView):
    model = Project
    template_name = "proman/project_detail.html"
    context_object_name = "project"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectDetailView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        super(TaskCreateView, self).get_initial()
        project = self.object.pk
        user = self.request.user
        self.initial = {"assignee":user.id, "project":project}
        return self.initial

    def get_context_data(self, **kwargs):
        project = self.object.pk
        user = self.request.user
        form = TaskMiniForm()
        form.fields['assignee'].initial = user.id
        form.fields['project'].initial = project
        context = super(ProjectDetailView, self).get_context_data(**kwargs)

        context['form'] = form
        context['project_tasks_stuck'] = Task.objects.filter(version=False, project=self.kwargs['pk'], status="stuck").annotate(hours=Sum('task_time')).order_by('due_dt')
        context['project_tasks_stuck_hours'] = context['project_tasks_stuck'].aggregate(total=Sum('task_time'))

        context['project_tasks_in_progress'] = Task.objects.filter(version=False, project=self.kwargs['pk'], status="in progress").annotate(hours=Sum('task_time')).order_by('due_dt')
        context['project_tasks_in_progress_hours'] = context['project_tasks_in_progress'].aggregate(total=Sum('task_time'))

        context['project_tasks_not_started'] = Task.objects.filter(version=False, project=self.kwargs['pk'], status="not started").order_by('due_dt')
        context['project_tasks_not_started_hours'] = context['project_tasks_not_started'].aggregate(total=Sum('task_time'))

        context['project_tasks_done'] = Task.objects.filter(version=False, project=self.kwargs['pk'], status="done").order_by('due_dt')
        context['project_tasks_done_hours'] = context['project_tasks_done'].aggregate(total=Sum('task_time'))

        return context

