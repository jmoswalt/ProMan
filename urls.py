from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from promon import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', TemplateView.as_view(template_name="home.html"), name='home'),

    # People
    url(r'^people/(?P<username>\w+)/$', views.UserDetailView.as_view(), name='user_detail'),
    url(r'^people/$', views.UserListView.as_view(), name='users'),

    # Projects
    url(r'^projects/add/$', views.ProjectCreateView.as_view(), name='project_create'),
    url(r'^projects/edit/(?P<pk>\d+)/$', views.ProjectUpdateView.as_view(), name='project_update'),
    url(r'^projects/(?P<pk>\d+)/$', views.ProjectDetailView.as_view(), name='project_detail'),
    url(r'^projects/$', views.ProjectListView.as_view(), name='projects'),

    # Tasks
    url(r'^tasks/add/$', views.TaskCreateView.as_view(), name='task_create'),
    url(r'^tasks/edit/(?P<pk>\d+)/$', views.TaskUpdateView.as_view(), name='task_update'),
    url(r'^tasks/(?P<pk>\d+)/$', views.TaskDetailView.as_view(), name='task_detail'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
