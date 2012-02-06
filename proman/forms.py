from datetime import datetime, timedelta
from django import forms
from django.contrib.admin import widgets
from proman.models import Task, Project

DUE_DT_INITIAL = datetime.now() + timedelta(weeks=1)

class TaskForm(forms.ModelForm):
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

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(version=False)
        self.fields['due_dt'].initial = DUE_DT_INITIAL
        self.fields['due_dt'].widget = widgets.AdminSplitDateTime()

class ProjectForm(forms.ModelForm):
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

class TaskMiniForm(forms.ModelForm):
    assignee = forms.CharField(widget=forms.HiddenInput)

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

    def __init__(self, *args, **kwargs):
        super(TaskMiniForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(version=False)
        self.fields['due_dt'].initial = DUE_DT_INITIAL
