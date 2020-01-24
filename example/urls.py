import django.contrib.auth.views
from django.conf.urls import include, handler500, url
from django.conf import settings

import authority.views
import authority.urls
import example.exampleapp.views

from exampleapp.forms import SpecialUserPermissionForm

authority.autodiscover()

handler500  # flake8

urlpatterns = (
    url(
        r'^authority/permission/add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$',  # noqa
        view=authority.views.add_permission,
        name="authority-add-permission",
        kwargs={'approved': True, 'form_class': SpecialUserPermissionForm}
    ),
    url(
        r'^request/add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$',  # noqa
        view=authority.views.add_permission,
        name="authority-add-permission-request",
        kwargs={'approved': False, 'form_class': SpecialUserPermissionForm}
    ),
    url(r'^authority/', include(authority.urls)),
    url(r'^accounts/login/$', django.contrib.auth.views.LoginView.as_view()),
    url(
        r'^(?P<url>[\/0-9A-Za-z]+)$',
        example.exampleapp.views.top_secret,
        {'lala': 'oh yeah!'},
    ),
)

if settings.DEBUG:
    urlpatterns += (
        url(r'^media/(?P<path>.*)$', django.views.static.serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
