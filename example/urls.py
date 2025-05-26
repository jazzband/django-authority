import django.contrib.auth.views
from django.conf.urls import include, handler500
from django.conf import settings
from django.urls import re_path

import authority.views
import authority.urls
import example.exampleapp.views

from exampleapp.forms import SpecialUserPermissionForm

authority.autodiscover()

handler500  # flake8

urlpatterns = (
    re_path(
        r"^authority/permission/add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$",  # noqa
        view=authority.views.add_permission,
        name="authority-add-permission",
        kwargs={"approved": True, "form_class": SpecialUserPermissionForm},
    ),
    re_path(
        r"^request/add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$",  # noqa
        view=authority.views.add_permission,
        name="authority-add-permission-request",
        kwargs={"approved": False, "form_class": SpecialUserPermissionForm},
    ),
    re_path(r"^authority/", include(authority.urls)),
    re_path(r"^accounts/login/$", django.contrib.auth.views.LoginView.as_view()),
    re_path(
        r"^(?P<url>[\/0-9A-Za-z]+)$",
        example.exampleapp.views.top_secret,
        {"lala": "oh yeah!"},
    ),
)

if settings.DEBUG:
    urlpatterns += (
        re_path(
            r"^media/(?P<path>.*)$",
            django.views.static.serve,
            {"document_root": settings.MEDIA_ROOT,},
        ),
    )
