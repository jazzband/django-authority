from inspect import isfunction, getmembers
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.db.models.base import ModelBase
from django.contrib.contenttypes.models import ContentType
from authority.models import Permission

registry = {}

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

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
        if new_class in registry:
            raise AlreadyRegistered(
                "The permission %s is already registered" % new_class)
        if new_class.label in registry.values():
            raise ImproperlyConfigured(
                "The name of %s conflicts with %s" % \
                    (new_class, registry[new_class.label]))
        # registry[PollPermission] = Poll
        registry[new_class] = new_class.label
        if new_class.checks is None:
            new_class.checks = ()
        # automatically add following default checks and the other
        all_checks =  ['add', 'change', 'delete'] + list(new_class.checks)
        for check_name in all_checks:
            def func(self, obj=None):
                if obj is None:
                    obj = self.model
                # first check Django's permission system
                perm = '%s.%s_%s' % (obj._meta.app_label, # polls.add_poll
                                     check_name.lower(),
                                     obj._meta.object_name.lower())
                perms = self.has_perm(perm)
                if obj is not None and not isinstance(obj, ModelBase):
                    # only check the authority if not model instance
                    return (perms or
                            self.can_admin(obj) or
                            self.has_perm(perm, obj))
                return perms
            setattr(new_class, 'can_%s' % check_name.lower(), func)
        return new_class

def get_permission_by_label(label):
    for perm_cls, perm_label in registry.items():
        if perm_label == label:
            return perm_cls
    return None

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

    @classmethod
    def signature(cls):
        """
        Used to determine the name of the permission class which then can be
        used in the template tag to check.

        Format: <app_label>.<object_name>
                e.g. "polls.poll"
        """
        return '%s.%s' % (cls.model._meta.app_label,
                          cls.model._meta.object_name.lower())

    def has_user_perms(self, perm, obj, check_groups=True):
        if self.user:
            if self.user.is_superuser:
                return True
            if not self.user.is_active:
                return False
            # check if a Permission object exists for the given params
            print obj
            content_type = ContentType.objects.get_for_model(obj)
            perms = Permission.objects.filter(user=self.user, codename=perm,
                                              content_type=content_type,
                                              object_id=obj.id)
            if perms:
                return True
            if check_groups:
                # look if one of the user's group have the permissions
                for group in self.user.groups.all():
                    if self.has_group_perms(perm, obj):
                        return True
        return False

    def has_group_perms(self, perm, obj):
        """
        Check if group has the permission for the given object
        """
        perms = self.get_group_perms(perm, obj).filter(object_id=obj.id)
        if perms:
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

    def get_perms(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        perms = Permission.objects.filter(
            Q(user=self.user) | Q(
                group__in=self.user.groups.all()
            ), content_type=content_type)
        return perms
    
    def get_user_perms(self, perm, obj):
        """
        Get objects that User perm permission on
        """
        perms = self.get_perms(obj)
        return perms.filter(codename=perm)

    def get_group_perms(self, perm, obj):
        """
        Get objects that Group perm permission on
        """
        content_type = ContentType.objects.get_for_model(obj)
        perms = Permission.objects.filter(group=self.group, codename=perm,
                                          content_type=content_type)
        return perms

    def clean_perms(self, obj):
        """
        Delete permissions related to an object instance
        """
        perms = self.get_perms(obj)
        perms.delete()

    def can_admin(self, obj):
        return self.has_perm('%s.admin' % obj._meta.app_label, obj)
