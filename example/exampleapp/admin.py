from django.contrib import admin
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.admin import FlatPageAdmin
from authority.admin import PermissionInline

admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin, inlines=[PermissionInline])
