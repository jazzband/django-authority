from django.conf.urls.defaults import *
from authority.views import (add_permission, delete_permission,
                             approve_permission_request)

urlpatterns = patterns('',
    url(r'^add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$', add_permission, name="authority-add-permission", kwargs = {'approved': True }),
    url(r'^add-request/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$', add_permission, name="authority-add-request", kwargs = {'approved': False }),
    url(r'^approve-request/(?P<permission_pk>\d+)/$', approve_permission_request, name="authority-approve-request"),
    url(r'^delete-request/(?P<permission_pk>\d+)/$', delete_permission, name="authority-delete-request", kwargs = {'approved': False }),
    url(r'^delete/(?P<permission_pk>\d+)/$', delete_permission, name="authority-delete-permission", kwargs = {'approved': True }),
)
