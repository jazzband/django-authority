from django.urls import re_path
from authority.views import (
    add_permission,
    approve_permission_request,
    delete_permission,
)


urlpatterns = [
    re_path(
        r"^permission/add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$",
        view=add_permission,
        name="authority-add-permission",
        kwargs={"approved": True},
    ),
    re_path(
        r"^permission/delete/(?P<permission_pk>\d+)/$",
        view=delete_permission,
        name="authority-delete-permission",
        kwargs={"approved": True},
    ),
    re_path(
        r"^request/add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$",
        view=add_permission,
        name="authority-add-permission-request",
        kwargs={"approved": False},
    ),
    re_path(
        r"^request/approve/(?P<permission_pk>\d+)/$",
        view=approve_permission_request,
        name="authority-approve-permission-request",
    ),
    re_path(
        r"^request/delete/(?P<permission_pk>\d+)/$",
        view=delete_permission,
        name="authority-delete-permission-request",
        kwargs={"approved": False},
    ),
]
