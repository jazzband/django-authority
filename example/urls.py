
from django.conf.urls.defaults import patterns, include, handler500
from django.conf import settings
from django.contrib import admin
import authority

admin.autodiscover()
authority.autodiscover()

handler500 # Pyflakes

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^perms/', include('authority.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
