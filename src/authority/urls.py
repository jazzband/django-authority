from django.conf.urls.defaults import *
from authority.views import add_permission, delete_permission

urlpatterns = patterns('',
    url(r'^add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$', add_permission, name="authority-add-permission"),
    url(r'^delete/(?P<permission_pk>\d+)/$', delete_permission, name="authority-delete-permission"),
)
