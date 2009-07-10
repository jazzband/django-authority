from django import forms
from django.contrib import admin
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst, truncate_words

from authority.models import Permission
from authority.widgets import GenericForeignKeyRawIdWidget
from authority import get_choices_for

class PermissionInline(generic.GenericTabularInline):
    model = Permission
    raw_id_fields = ('user', 'group', 'creator')
    extra = 1

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'codename':
            perm_choices = get_choices_for(self.parent_model)
            kwargs['label'] = _('permission')
            kwargs['widget'] = forms.Select(choices=perm_choices)
            return db_field.formfield(**kwargs)
        return super(PermissionInline, self).formfield_for_dbfield(db_field, **kwargs)

class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'content_type', 'user', 'group')
    list_filter = ('content_type',)
    search_fields = ('user__username', 'group__name', 'codename')
    raw_id_fields = ('user', 'group', 'creator')
    generic_fields = ('content_object',)
    fieldsets = (
        (None, {
            'fields': ('codename', ('content_type', 'object_id'))
        }),
        (_('granted'), {
            'fields': ('creator', ('user', 'group'),)
        }),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        # For generic foreign keys marked as generic_fields we use a special widget 
        if db_field.name in [f.fk_field for f in self.model._meta.virtual_fields if f.name in self.generic_fields]: 
            for gfk in self.model._meta.virtual_fields: 
                if gfk.fk_field == db_field.name: 
                    return db_field.formfield(
                        widget=GenericForeignKeyRawIdWidget(
                            gfk.ct_field, self.admin_site._registry.keys()))
        return super(PermissionAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def queryset(self, request):
        user = request.user
        if user.is_superuser or \
                user.has_perm('permissions.change_foreign_permissions'):
            return super(PermissionAdmin, self).queryset(request)
        return super(PermissionAdmin, self).queryset(request).filter(creator=user)

admin.site.register(Permission, PermissionAdmin)
