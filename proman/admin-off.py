from django.contrib import admin
from django.utils.encoding import iri_to_uri

from proman.models import Project, Task
from proman.forms import TaskForm



class ProjectAdmin(admin.ModelAdmin):
    model = Project
    list_display = ['name', 'technology', 'owner']
    list_filter = ['technology', 'status']
    prepopulated_fields = {'start_dt': ['name']}
    
    fieldsets = (
        (None, {'fields': (
            'name',
            'description',
            'owner',
            'start_dt',
            'end_dt',
            'task_budget',
            'technology',
            'status',
            'ongoing',
        )}),
    )

    def save_model(self, request, object, form, change):
        """
        add the necessary versioning information
        """
        if change:
            # make new object and save it
            obj = form.save(commit=False)
            orig = Project.objects.get(pk=obj.pk)
            new_obj = orig
            new_obj.pk = None
            new_obj.editor = request.user
            new_obj.version = True
            new_obj.save()
            obj.save()
        else:
            obj = form.save(commit=False)
            obj.original_creator = request.user
            obj.editor = request.user
            obj.save()
            obj.original = obj
            obj.save()

        return obj

    def change_view(self, request, object_id, extra_context=None):
        result = super(ProjectAdmin, self).change_view(request, object_id, extra_context)

        if not request.POST.has_key('_addanother') and not request.POST.has_key('_continue') and request.GET.has_key('next'):
            result['Location'] = iri_to_uri("%s") % request.GET.get('next')
        return result


class TaskAdmin(admin.ModelAdmin):
    model = Task
    list_display = ['title', 'due_dt', 'assignee', 'task_time']
    list_filter = ['status']
    form = TaskForm
    
    fieldsets = (
        (None, {'fields': (
            'title',
            'project',
            'assignee',
            'due_dt',
            'description',
            'task_time',
            'billable',
            'status',
            'resolution',
            'private',
        )}),
    )

    def save_model(self, request, object, form, change):
        """
        add the necessary versioning information
        """
        if change:
            # make new object and save it
            obj = form.save(commit=False)
            orig = Task.objects.get(pk=obj.pk)
            new_obj = orig
            new_obj.pk = None
            new_obj.editor = request.user
            new_obj.version = True
            new_obj.save()
            obj.save()
        else:
            obj = form.save(commit=False)
            obj.original_creator = request.user
            obj.editor = request.user
            obj.save()
            obj.original = obj
            obj.save()

        return obj

    def change_view(self, request, object_id, extra_context=None):
        print "GEREERER"
        result = super(TaskAdmin, self).change_view(request, object_id, extra_context)
        print request.GET

        if not request.POST.has_key('_addanother') and not request.POST.has_key('_continue') and request.GET.has_key('next'):
            print request.GET.get('next')
            result['Location'] = iri_to_uri("%s") % request.GET.get('next')
        return result


admin.site.register(Task, TaskAdmin)
admin.site.register(Project, ProjectAdmin)