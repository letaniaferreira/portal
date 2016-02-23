from django.conf.urls import include, url, patterns
from django.views.generic.base import TemplateView

urlpatterns = patterns('designsafe.apps.notifications.views',
    url(r'^$', 'index', name='index'),
    url(r'^jobs/$', 'job_notification_handler', name='job_notification_handler'),
    url(r'^notifications/$', 'notifications', name='notifications'),
    url(r'^delete/$', 'delete_notification', name='delete_notification'),

    # url(r'^apps-list/$', 'apps_list', name='apps_list'),
    # url(r'^files-list/$', 'files_list', name='files_list'),
    # url(r'^jobs-list/$', 'jobs_list', name='jobs_list'),
    # url(r'^jobs-details/$', 'jobs_details', name='jobs_details'),
)
