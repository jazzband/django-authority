from django import forms
from django.contrib import admin
from django.contrib.contenttypes import generic

from authority.models import Permission
from authority import permissions

class PermissionInline(generic.GenericTabularInline):
    model = Permission
    extra = 1
    raw_id_fields = ('user', 'group', 'creator')

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'codename':
            perm_choices = permissions.registry.get_choices_for(self.parent_model)
            kwargs['widget'] = forms.Select(choices=perm_choices)
            return db_field.formfield(**kwargs)
        return super(PermissionInline, self).formfield_for_dbfield(db_field,**kwargs)

class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'content_type', 'user', 'group')
    list_filter = ('codename', 'content_type')
    search_fields = ['object_id', 'content_type', 'user', 'group']
    raw_id_fields = ['user', 'group']

    fieldsets = (
        (None, {
            'fields': ('codename', ('content_type', 'object_id'))
        }),
        ('granted for', {
            'fields': ('user', 'group', 'creator')
        }),
    )

    def queryset(self, request):
        user = request.user
        if user.is_superuser or \
                user.has_perm('permissions.change_foreign_permissions'):
            return super(PermissionAdmin, self).queryset(request)
        return super(PermissionAdmin, self).queryset(request).filter(creator=user)

admin.site.register(Permission, PermissionAdmin)
