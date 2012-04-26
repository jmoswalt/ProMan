from datetime import datetime, timedelta
from django import forms
from django.contrib.admin import widgets
from django.utils import timezone
from proman.models import Task, Project

DUE_DT_INITIAL = timezone.now() + timedelta(weeks=1)

class TaskForm(forms.ModelForm):
    due_dt = forms.CharField(widget=forms.DateTimeInput(format='%m/%d/%Y'))

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
            'status',
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

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(version=False)

class ProjectForm(forms.ModelForm):
    start_dt = forms.CharField(widget=forms.DateTimeInput(format='%m/%d/%Y'))
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
            'status',
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
        self.fields['due_dt'].initial = DUE_DT_INITIAL

class TaskCloseForm(forms.ModelForm):
    status = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = Task

        fields = (
            'status',
            'task_time',
            'resolution',
        )

    def __init__(self, *args, **kwargs):
        super(TaskCloseForm, self).__init__(*args, **kwargs)

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if status:
            return "Done"
        return status
