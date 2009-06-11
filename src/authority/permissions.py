from inspect import getmembers, ismethod
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.db.models.base import ModelBase
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from authority.models import Permission

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

class PermissionRegistry(dict):
    """
    A dictionary that contains permission instances and their labels.
    """
    def get_permission_by_label(self, label):
        for perm_cls, perm_label in self.items():
            if perm_label == label:
                return perm_cls
        return None

    def _choices(self, perm, default=BLANK_CHOICE_DASH):
        choices = [] + default
        for name, check in getmembers(perm, ismethod):
            if name in perm.checks:
                signature = '%s.%s' % (perm.label, name)
                label = getattr(check, 'verbose_name', signature)
                choices.append((signature, label))
        return choices

    def get_choices_for(self, obj):
        choices = []
        for perm in [perm for perm in self if perm.model == obj.__class__]:
            perm_label = '%s.%s.%s' % (obj._meta.app_label,
                                       obj._meta.object_name.lower(),
                                       obj.pk)
            choices += self._choices(perm)
        return choices
registry = PermissionRegistry()

class PermissionMetaclass(type):
    """
    Used to generate the default set of permission checks "add", "change" and
    "delete".
    """
    def __new__(cls, name, bases, attrs):
        new_class = super(
            PermissionMetaclass, cls).__new__(cls, name, bases, attrs)
        if new_class.__name__ == "BasePermission":
            return new_class
        if not new_class.model:
            raise ImproperlyConfigured(
                "Permission %s requires a model attribute." % new_class)
        if not new_class.label:
            new_class.label = "%s_permission" % new_class.__name__.lower()
        new_class.label = slugify(new_class.label)
        if new_class in registry:
            raise AlreadyRegistered(
                "The permission %s is already registered" % new_class)
        if new_class.label in registry.values():
            raise ImproperlyConfigured(
                "The name of %s conflicts with %s" % \
                    (new_class, registry[new_class.label]))
        registry[new_class] = new_class.label
        if new_class.checks is None:
            new_class.checks = []
        new_class.checks = list(new_class.checks)
        for check_name in ['add', 'browse', 'change', 'delete']:
            def func(self, obj=None):
                if obj is None:
                    obj = self.model
                # first check Django's permission system
                perm = '%s.%s_%s' % (obj._meta.app_label, # polls.add_poll
                                     check_name.lower(),
                                     obj._meta.object_name.lower())
                perms = None
                if self.user:
                    perms = self.user.has_perm(perm)
                if obj is not None and not isinstance(obj, ModelBase):
                    # only check the authority if not model instance
                    return (perms or
                            self.can_admin(obj) or
                            self.has_perm(perm, obj))
                return perms
            func.verbose_name = _('Can %(check)s this %(object_name)s' % {
                'object_name': new_class.model._meta.object_name.lower(),
                'check': check_name.lower()})
            func_name = 'can_%s' % check_name.lower()
            if func_name not in new_class.checks:
                new_class.checks.append(func_name)
            setattr(new_class, func_name, func)
        return new_class

class BasePermission(object):
    """
    Base Permission class to be used to define app permissions.

    check = BasePermission(request.user)
    """
    __metaclass__ = PermissionMetaclass

    checks = ()
    label = None
    model = None

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
            if perms.filter(object_id=obj.id):
                return True
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

    def can_admin(self, obj):
        return self.has_perm('%s.admin' % obj._meta.app_label, obj)
