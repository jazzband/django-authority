from inspect import getmembers, ismethod
from django.db.models import Q
from django.db.models.base import ModelBase
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
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

    def get_check(self, user, label):
        perm_label, check_name = label.split('.')
        perm_cls = self.get_permission_by_label(perm_label)
        perm_instance = perm_cls(user)
        return getattr(perm_instance, check_name, None)

    def get_permissions_by_model(self, model):
        return [perm for perm in self if perm.model == model]

    def get_choices_for(self, obj, default=BLANK_CHOICE_DASH):
        choices = [] + default
        model_cls = obj
        if not isinstance(obj, ModelBase):
            model_cls = obj.__class__
        for perm in self.get_permissions_by_model(model_cls):
            for name, check in getmembers(perm, ismethod):
                if name in perm.checks:
                    signature = '%s.%s' % (perm.label, name)
                    label = getattr(check, 'short_description', signature)
                    choices.append((signature, label))
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
        generic_checks = ['add', 'browse', 'change', 'delete']
        for check_name in new_class.checks:
            check_func = getattr(new_class, check_name, None)
            if check_func is not None:
                func = new_class.create_check(check_name, check_func)
                func.__name__ = check_name
                func.short_description = getattr(check_func, 'short_description',
                    _("%(object_name)s permission '%(check)s'") % {
                        'object_name': new_class.model._meta.object_name,
                        'check': check_name.lower()})
                setattr(new_class, check_name, func)
            else:
                generic_checks.append(check_name)
        for check_name in generic_checks:
            func = new_class.create_check(check_name, generic=True)
            object_name = new_class.model._meta.object_name
            func_name = "%s_%s" % (check_name.lower(), object_name.lower())
            func.short_description = _("Can %(check)s this %(object_name)s") % {
                'object_name': new_class.model._meta.object_name.lower(),
                'check': check_name.lower()}
            func.check_name = check_name
            if func_name not in new_class.checks:
                new_class.checks.append(func_name)
            setattr(new_class, func_name, func)
        return new_class

    def _create_check(cls, check_name, check_func=None, generic=False):
        def check(self, obj=None, *args, **kwargs):
            if obj is None:
                return False
            granted = self.can(check_name.lower(), obj, generic=generic)
            if check_func and not granted:
                return check_func(self, obj, *args, **kwargs)
            return granted
        return check
    create_check = classmethod(_create_check)

class BasePermission(object):
    """
    Base Permission class to be used to define app permissions.

    check = MyPermission(request.user)
    if check.can("change", obj):
        
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
                check_groups).filter(object_id=obj.id).count()
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

    def can(self, check, obj=None, generic=False):
        if obj is None:
            obj = self.model
        # first check Django's permission system
        perm = '%s.%s' % (self.label, check.lower())
        if generic:
            perm = '%s_%s' % (perm, obj._meta.object_name.lower())
        perms = None
        if self.user:
            perms = self.user.has_perm(perm)
        if obj is not None and not isinstance(obj, ModelBase):
            # only check the authority if not model instance
            return perms or self.has_perm(perm, obj)
        return perms
