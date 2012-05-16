from datetime import datetime, timedelta
from django import forms
from django.contrib.admin import widgets
from django.utils import timezone
from django.contrib.auth.models import User
from proman.models import Task, Project, Profile

DUE_DT_INITIAL = timezone.now() + timedelta(weeks=1)
COMPLETED_DT_INITIAL = timezone.now()

class TaskForm(forms.ModelForm):
    due_dt = forms.CharField(widget=forms.DateTimeInput(format='%m/%d/%Y'), label="Due Date")
    completed_dt = forms.CharField(widget=forms.DateTimeInput(format='%m/%d/%Y'), label="Completion Date", required=False)

    class Meta:
        model = Task

        fields = (
            'title',
            'project',
            'assignee',
            'due_dt',
            'description',
            'task_time',
            'billable',
            'stuck',
            'private',
            'resolution',
        )

    def clean_due_dt(self):
        due_dt = self.cleaned_data.get('due_dt')
        if due_dt:
            try:
                due_dt = datetime.strptime(due_dt, '%m/%d/%Y')
                due_dt = timezone.make_aware(due_dt, timezone.utc)
            except ValueError:
                due_dt = None
                self._errors['due_dt'] = ['Invalid date selected.']
        return due_dt

    def clean_completed_dt(self):
        completed_dt = self.cleaned_data.get('completed_dt')
        if completed_dt:
            try:
                completed_dt = datetime.strptime(completed_dt, '%m/%d/%Y')
                completed_dt = timezone.make_aware(completed_dt, timezone.utc)
            except ValueError:
                completed_dt = None
                self._errors['completed_dt'] = ['Invalid date selected.']
        return completed_dt

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(version=False)
        self.fields['assignee'].queryset = Profile.objects.filter(role="employee", user__is_active=True)

class ProjectForm(forms.ModelForm):
    start_dt = forms.CharField(widget=forms.DateTimeInput(format='%m/%d/%Y'), label="Start Date")
    end_dt = forms.CharField(widget=forms.DateTimeInput(format='%m/%d/%Y'), label="End Date", required=False)

    class Meta:
        model = Project

        fields = (
            'name',
            'description',
            'owner',
            'start_dt',
            'end_dt',
            'task_budget',
            'technology',
            'status',
            'ongoing',
        )

    def clean_start_dt(self):
        start_dt = self.cleaned_data.get('start_dt')
        if start_dt:
            try:
                start_dt = datetime.strptime(start_dt, '%m/%d/%Y')
                start_dt = timezone.make_aware(start_dt, timezone.utc)
            except ValueError:
                start_dt = None
                self._errors['start_dt'] = ['Invalid date selected.']
        return start_dt

    def clean_end_dt(self):
        end_dt = self.cleaned_data.get('end_dt')
        if end_dt:
            try:
                end_dt = datetime.strptime(end_dt, '%m/%d/%Y')
                end_dt = timezone.make_aware(end_dt, timezone.utc)
            except ValueError:
                end_dt = None
                self._errors['end_dt'] = ['Invalid date selected.']
        return end_dt

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        # Restrict the list of potential Owners to active employees
        active_employees = Profile.objects.filter(role="employee", user__is_active=True)
        self.fields['owner'].queryset = active_employees

        # If we have an instance, be sure to add the current owner in case they
        # are not currently an active employee.
        if self.instance:
            owner_qs = Profile.objects.filter(pk=self.instance.owner_id)
            self.fields['owner'].queryset = owner_qs | active_employees

    def save(self, *args, **kwargs):
        project = super(ProjectForm, self).save(*args, **kwargs)
        if not self.cleaned_data.get('end_dt'):
            project.end_dt = None
        return project

class TaskMiniForm(forms.ModelForm):
    project = forms.CharField(widget=forms.HiddenInput)
    due_dt = forms.CharField(widget=forms.DateTimeInput(format='%m/%d/%Y'), label="Due Date")

    class Meta:
        model = Task

        fields = (
            'title',
            'due_dt',
            'task_time',
            'description',
            'billable',
            'assignee',
            'project',
        )

    def clean_due_dt(self):
        due_dt = self.cleaned_data.get('due_dt')
        if due_dt:
            try:
                due_dt = datetime.strptime(due_dt, '%m/%d/%Y')
                due_dt = timezone.make_aware(due_dt, timezone.utc)
            except ValueError:
                due_dt = None
                self._errors['due_dt'] = ['Invalid date selected.']
        return due_dt

    def __init__(self, *args, **kwargs):
        super(TaskMiniForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(version=False)
        self.fields['assignee'].queryset = Profile.objects.filter(role="employee", user__is_active=True)

class TaskCloseForm(forms.ModelForm):
    completed = forms.BooleanField(widget=forms.HiddenInput, required=False)
    completed_dt = forms.CharField(widget=forms.DateTimeInput(format='%m/%d/%Y'), label="Completion Date")

    class Meta:
        model = Task

        fields = (
            'completed',
            'task_time',
            'completed_dt',
            'resolution',
        )

    def clean_completed_dt(self):
        completed_dt = self.cleaned_data.get('completed_dt')
        if completed_dt:
            try:
                completed_dt = datetime.strptime(completed_dt, '%m/%d/%Y')
                completed_dt = timezone.make_aware(completed_dt, timezone.utc)
            except ValueError:
                completed_dt = None
                self._errors['completed_dt'] = ['Invalid date selected.']
        return completed_dt

    def __init__(self, *args, **kwargs):
        super(TaskCloseForm, self).__init__(*args, **kwargs)

    def clean_completed(self):
        return True

class ProfileForm(forms.ModelForm):
    username = forms.CharField(help_text="Username defaults to email address if left empty.")

    class Meta:
        model = Profile

        fields = (
            'first_name',
            'last_name',
            'email',
            'username',
            'phone',
            'title',
            'role',
            'team',
            'team_leader',
            'client',
        )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if self.instance.user.username != username:
                try:
                    User.objects.get(username=username)
                    self._errors['username'] = 'That username is already taken. Please pick a different one.'
                except:
                    pass
        return username
