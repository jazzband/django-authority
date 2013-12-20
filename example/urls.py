try:
    from django.conf.urls import patterns, include, handler500, url
except ImportError:  # django < 1.4
    from django.conf.urls.defaults import patterns, include, handler500, url
from django.conf import settings
from django.contrib import admin
import authority

admin.autodiscover()
authority.autodiscover()

handler500 # Pyflakes

from exampleapp.forms import SpecialUserPermissionForm

urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    #('^admin/', include(admin.site.urls)),
    url(r'^authority/permission/add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$',
        view='authority.views.add_permission',
        name="authority-add-permission",
        kwargs={'approved': True, 'form_class': SpecialUserPermissionForm}
    ),
    url(r'^request/add/(?P<app_label>[\w\-]+)/(?P<module_name>[\w\-]+)/(?P<pk>\d+)/$',
        view='authority.views.add_permission',
        name="authority-add-permission-request",
        kwargs={'approved': False, 'form_class': SpecialUserPermissionForm}
    ),
    (r'^authority/', include('authority.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^(?P<url>[\/0-9A-Za-z]+)$', 'example.exampleapp.views.top_secret', {'lala': 'oh yeah!'}),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
