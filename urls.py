from django.conf.urls.defaults import *
from django.views.generic import TemplateView
from registration import urls as reg_urls

from proman import views, signals

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', TemplateView.as_view(template_name="home.html"), name='home'),

    # People
    url(r'^me/$', views.UserCurrent, name='user_current'),
    url(r'^people/id/(?P<pk>\d+)/$', views.UserIdRedirect, name='user_detail_pk'),
    url(r'^people/add/$', views.UserCreateView.as_view(), name='user_create'),
    url(r'^people/update/(?P<pk>\d+)/$', views.UserUpdateView.as_view(), name='user_update'),
    url(r'^people/(?P<username>[\w\@\.\-]+)/$', views.UserDetailView.as_view(), name='user_detail'),
    url(r'^people/$', views.UserListView.as_view(), name='users'),

    # Projects
    url(r'^projects/add/$', views.ProjectCreateView.as_view(), name='project_create'),
    url(r'^projects/update/(?P<pk>\d+)/$', views.ProjectUpdateView.as_view(), name='project_update'),
    url(r'^projects/(?P<pk>\d+)/$', views.ProjectDetailView.as_view(), name='project_detail'),
    url(r'^projects/$', views.ProjectListView.as_view(), name='projects'),

    # Tasks
    url(r'^tasks/add/$', views.TaskCreateView.as_view(), name='task_create'),
    url(r'^tasks/update/(?P<pk>\d+)/$', views.TaskUpdateView.as_view(), name='task_update'),
    url(r'^tasks/close/(?P<pk>\d+)/$', views.TaskCloseUpdateView.as_view(), name='task_close'),
    url(r'^tasks/(?P<pk>\d+)/$', views.TaskDetailView.as_view(), name='task_detail'),

    # Client Contacts
    url(r'^contacts/$', views.ContactListView.as_view(), name='contacts'),

    # Import from Harvest
    url(r'^import/(?P<content_type>[\w]+)/$', views.import_content, name='import_content'),
    url(r'^import/check/(?P<pk>\d+)/$', views.import_check, name='import_check'),
    url(r'^import/(?P<content_type>[\w]+)/(?P<pk>\d+)/$', views.import_content_attempt, name='import_content_attempt'),

    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'}, name='login'),
    url(r'^reset-password/$', 'django.contrib.auth.views.password_reset', name='password_reset'),
    url(r'^reset-password/done/$', 'django.contrib.auth.views.password_reset_done', {'template_name': 'admin/password_reset_done.html'}, name='password_reset_done'),
    # Waiting on 1.4 compatibility
    # url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
