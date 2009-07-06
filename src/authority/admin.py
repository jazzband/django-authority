from django import forms, template
from django.contrib import admin
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseForbidden, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import patterns, url
from django.db import models
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404, render_to_response

from authority.models import Permission
from authority import permissions

class PermissionInline(generic.GenericTabularInline):
    model = Permission
    raw_id_fields = ('user', 'group', 'creator')
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        self.current_user = request.user
        return super(PermissionInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'codename':
            perm_choices = permissions.registry.get_choices_for(self.parent_model)
            kwargs['label'] = _('permission')
            kwargs['widget'] = forms.Select(choices=perm_choices)
            return db_field.formfield(**kwargs)
        elif db_field.name == 'screator':
            field = db_field.formfield(**kwargs)
            field.initial = self.current_user.id
            return field
        return super(PermissionInline, self).formfield_for_dbfield(db_field, **kwargs)

class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'content_type', 'user', 'group')
    list_filter = ('codename', 'content_type')
    search_fields = ('user', 'group')
    raw_id_fields = ('user', 'group')
    fieldsets = (
        (None, {
            'fields': ('codename', ('content_type', 'object_id'))
        }),
        (_('granted'), {
            'fields': ('user', 'group', 'creator')
        }),
    )
    permission_change_form_template = None

    def queryset(self, request):
        user = request.user
        if user.is_superuser or \
                user.has_perm('permissions.change_foreign_permissions'):
            return super(PermissionAdmin, self).queryset(request)
        return super(PermissionAdmin, self).queryset(request).filter(creator=user)

admin.site.register(Permission, PermissionAdmin)
