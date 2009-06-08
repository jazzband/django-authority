from django.contrib.admin import site, ModelAdmin
from django.contrib.contenttypes import generic
from authority.models import Permission

class PermissionInline(generic.GenericTabularInline):
    model = Permission
    extra = 1
    #exclude = ('creator',)

class PermissionAdmin(ModelAdmin):
    model = Permission
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

site.register(Permission, PermissionAdmin)
