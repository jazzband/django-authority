from inspect import getmembers, ismethod
from django.db.models import Q
from django.db.models.base import Model, ModelBase
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from authority.models import Permission

class PermissionMetaclass(type):
    """
    Used to generate the default set of permission checks "add", "change" and
    "delete".
    """
    def __new__(cls, name, bases, attrs):
        new_class = super(
            PermissionMetaclass, cls).__new__(cls, name, bases, attrs)
        if not new_class.label:
            new_class.label = "%s_permission" % new_class.__name__.lower()
        new_class.label = slugify(new_class.label)
        if new_class.checks is None:
            new_class.checks = []
        # force check names to be lower case
        new_class.checks = [check.lower() for check in new_class.checks]
        return new_class

class BasePermission(object):
    """
    Base Permission class to be used to define app permissions.
    """
    __metaclass__ = PermissionMetaclass

    checks = ()
    label = None
    generic_checks = ['add', 'browse', 'change', 'delete']

    def __init__(self, user=None, group=None, *args, **kwargs):
        self.user = user
        self.group = group
        super(BasePermission, self).__init__(*args, **kwargs)

    def has_user_perms(self, perm, obj, check_groups=True):
        if self.user:
            if self.user.is_superuser:
                return True
            if not self.user.is_active:
                return False
            # check if a Permission object exists for the given params
            return Permission.objects.user_permissions(self.user, perm, obj,
                check_groups).filter(object_id=obj.id)
        return False

    def has_group_perms(self, perm, obj):
        """
        Check if group has the permission for the given object
        """
        if self.group:
            perms = Permission.objects.group_permissions(self.group, perm, obj)
            return perms.filter(object_id=obj.id)
        return False

    def has_perm(self, perm, obj, check_groups=True):
        """
        Check if user has the permission for the given object
        """
        if self.user:
            if self.has_user_perms(perm, obj, check_groups):
                return True
        if self.group:
            return self.has_group_perms(perm, obj)
        return False

    def can(self, check, generic=False, *args, **kwargs):
        if not args:
            args = [self.model]
        perms = False
        for obj in args:
            # skip this obj if it's not a model class or instance
            if not isinstance(obj, (ModelBase, Model)):
                continue
            # first check Django's permission system
            if self.user:
                perm = '%s.%s' % (obj._meta.app_label, check.lower())
                if generic:
                    perm = '%s_%s' % (perm, obj._meta.object_name.lower())
                perms = perms or self.user.has_perm(perm)
            perm = '%s.%s' % (self.label, check.lower())
            if generic:
                perm = '%s_%s' % (perm, obj._meta.object_name.lower())
            # then check authority's per object permissions
            if not isinstance(obj, ModelBase) and isinstance(obj, self.model):
                # only check the authority if obj is not a model class
                perms = perms or self.has_perm(perm, obj)
        return perms
