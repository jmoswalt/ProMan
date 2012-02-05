from datetime import date, timedelta
from django import forms
from promon.models import Task, Project

DUE_DT_INITIAL = date.today() + timedelta(weeks=1)

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

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project

        fields = (
            'name',
            'description',
            'project_owner',
            'start_dt',
            'end_dt',
            'task_budget',
            'technology',
            'status',
            'ongoing',
        )

class TaskMiniForm(forms.ModelForm):
    project = forms.CharField(widget=forms.HiddenInput)
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
#         if 'project' in kwargs:
#             self.fields['project'].initial = kwargs['project']
#         if 'assignee' in kwargs:
#             self.fields['assignee'].initial = kwargs['assignee']
