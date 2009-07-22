from django import template
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse

from authority import permissions, get_check
from authority.models import Permission
from authority.forms import UserPermissionForm

register = template.Library()

def _base_link(context, perm, view_name):
    return {
        'next': context['request'].build_absolute_uri(),
        'url': reverse(view_name, kwargs={'permission_pk': perm.pk,}),
    }

def _base_permission_form(context, obj, perm, user, approved, view_name):
    return {
        'form': UserPermissionForm(perm, obj, approved, 
                                   initial=dict(codename=perm, user=user)),
        'form_url': url_for_obj(view_name, obj),
        'next': context['request'].build_absolute_uri(),
    }

def next_bit_for(bits, key, if_none=None):
    try:
        return bits[bits.index(key)+1]
    except ValueError:
        return if_none

class ResolverNode(template.Node):
    """
    A small wrapper that adds a convenient resolve method.
    """
    def resolve(self, var, context):
        """Resolves a variable out of context if it's not in quotes"""
        if var is None:
            return var
        if var[0] in ('"', "'") and var[-1] == var[0]:
            return var[1:-1]
        else:
            return template.Variable(var).resolve(context)

@register.simple_tag
def url_for_obj(view_name, obj):
    return reverse(view_name, kwargs={
            'app_label': obj._meta.app_label,
            'module_name': obj._meta.module_name,
            'pk': obj.pk})

@register.simple_tag
def add_url_for_obj(obj):
    return url_for_obj('authority-add-permission', obj)

class ComparisonNode(ResolverNode):
    """
    Implements a node to provide an "if user/group has permission on object"
    """
    def __init__(self, user, perm, nodelist_true, nodelist_false, *objs):
        self.user = user
        self.objs = objs
        self.perm = perm
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context):
        try:
            user = self.resolve(self.user, context)
            perm = self.resolve(self.perm, context)
            if self.objs:
                objs = []
                for obj in self.objs:
                    if obj is not None:
                        objs.append(self.resolve(obj, context))
            else:
                objs = None
            check = get_check(user, perm)
            if check is not None:
                if check(*objs):
                    # return True if check was successful
                    return self.nodelist_true.render(context)
        # If the app couldn't be found
        except (ImproperlyConfigured, ImportError):
            return ''
        # If either variable fails to resolve, return nothing.
        except template.VariableDoesNotExist:
            return ''
        # If the types don't permit comparison, return nothing.
        except (TypeError, AttributeError):
            return ''
        return self.nodelist_false.render(context)

@register.tag('ifhasperm')
def do_if_has_perm(parser, token):
    """
    This function provides functionality for the 'ifhasperm' template tag

    Syntax::

        {% ifhasperm [permission_label].[check_name] [user] [*objs] %}
            lalala
        {% else %}
            meh
        {% endifhasperm %}

        {% if hasperm "poll_permission.change_poll" request.user %}
            lalala
        {% else %}
            meh
        {% endifhasperm %}

    """
    bits = token.contents.split()
    if 5 < len(bits) < 3:
        raise template.TemplateSyntaxError("'%s' tag takes three, "
                                            "four or five arguments" % bits[0])
    end_tag = 'endifhasperm'
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else': # there is an 'else' clause in the tag
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()

    if len(bits) == 3: # this tag requires at most 2 objects . None is given
        objs = (None, None)
    elif len(bits) == 4:# one is given
        objs = (bits[3], None)
    else: #two are given
        objs = (bits[3], bits[4])
    return ComparisonNode(bits[2], bits[1], nodelist_true, nodelist_false, *objs)

@register.inclusion_tag('authority/permission_delete_link.html', takes_context=True)
def permission_delete_link(context, perm):
    """
    Renders a html link to the delete view of the given permission. Returns
    no content if the request-user has no permission to delete foreign
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        if user.has_perm('authority.delete_foreign_permissions') \
            or user.pk == perm.creator.pk:
            return _base_link(context, perm, 'authority-delete-permission')
    return {'url': None}


@register.inclusion_tag('authority/permission_form.html', takes_context=True)
def permission_form(context, obj, perm=None):
    """
    Renders an "add permissions" form for the given object. If no object
    is given it will render a select box to choose from.

    Syntax::

        {% permission_form [obj] [permission_label].[check_name] %}
        {% permission_form lesson "lesson_permission.add_lesson" %}

    """
    user = context['request'].user
    if user.is_authenticated():
        if user.has_perm('authority.add_permission'):
            return _base_permission_form(context, obj, perm, None, True, 
                                         'authority-add-permission')
    return {'form': None}


@register.inclusion_tag('authority/permission_request_form.html', takes_context=True)
def permission_request_form(context, obj, perm=None):
    """
    Renders an "add permission requests" form for the given object. If no perm
    is given it will render a select box to choose from.

    Syntax::

        {% permission_request_form [obj] [permission_label].[check_name] %}
        {% permission_request_form lesson "lesson_permission.add_lesson" %}

    """
    user = context['request'].user
    if user.is_authenticated() and not user.is_superuser:
        return _base_permission_form(context, obj, perm, user, False, 
                                     'authority-add-request')
    return {'form': None}


class PermissionsForObjectNode(ResolverNode):
    def __init__(self, obj, user, var_name, approved, perm=None, objs=None):
        self.obj = obj
        self.user = user
        self.perm = perm
        self.var_name = var_name
        self.approved = approved

    def render(self, context):
        obj = self.resolve(self.obj, context)
        var_name = self.resolve(self.var_name, context)
        user = self.resolve(self.user, context)
        perms = []
        if not isinstance(user, AnonymousUser):
            perms = Permission.objects.for_object(obj, self.approved)
            if isinstance(user, User):
                perms = perms.filter(user=user)
        context[var_name] = perms
        return ''

@register.tag
def get_permissions(parser, token):
    """
    Retrieves all permissions associated with the given obj and user
    and assigns the result to a context variable.
    
    Syntax::

        {% get_permissions obj %}
        {% for perm in permissions %}
            {{ perm }}
        {% endfor %}

        {% get_permissions obj as "my_permissions" %}
        {% get_permissions obj for request.user as "my_permissions" %}

    """
    bits = token.contents.split()
    kwargs = {
        'obj': next_bit_for(bits, 'get_permissions'),
        'user': next_bit_for(bits, 'for'),
        'var_name': next_bit_for(bits, 'as', '"permissions"'),
        'approved': True,
    }
    return PermissionsForObjectNode(**kwargs)


@register.tag
def get_permission_requests(parser, token):
    """
    Retrieves all permissions requests associated with the given obj and user
    and assigns the result to a context variable.
    
    Syntax::

        {% get_permission_requests obj %}
        {% for perm in permissions %}
            {{ perm }}
        {% endfor %}

        {% get_permission_requests obj as "my_permissions" %}
        {% get_permission_requests obj for request.user as "my_permissions" %}

    """
    bits = token.contents.split()
    kwargs = {
        'obj': next_bit_for(bits, 'get_permission_requests'),
        'user': next_bit_for(bits, 'for'),
        'var_name': next_bit_for(bits, 'as', '"permission_requests"'),
        'approved': False,
    }
    return PermissionsForObjectNode(**kwargs)

class PermissionForObjectNode(ResolverNode):
    def __init__(self, perm, user, objs, var_name):
        self.perm = perm
        self.user = user
        self.objs = objs
        self.var_name = var_name

    def render(self, context):
        objs = [self.resolve(obj, context) for obj in self.objs.split(',')]
        var_name = self.resolve(self.var_name, context)
        perm = self.resolve(self.perm, context)
        user = self.resolve(self.user, context)
        granted = False
        if not isinstance(user, AnonymousUser):
            check = get_check(user, perm)
            if check is not None:
                granted = check(*objs)
        context[var_name] = granted
        return ''

@register.tag
def get_permission(parser, token):
    """
    Performs a permission check with the given signature, user and objects
    and assigns the result to a context variable.

    Syntax::

        {% get_permission [permission_label].[check_name] for [user] and [objs] as [varname] %}

        {% get_permission "poll_permission.change_poll" for request.user and poll as "is_allowed" %}
        {% get_permission "poll_permission.change_poll" for request.user and poll,second_poll as "is_allowed" %}
        
        {% if is_allowed %}
            I've got ze power to change ze pollllllzzz. Muahahaa.
        {% else %}
            Meh. No power for meeeee.
        {% endif %}

    """
    bits = token.contents.split()
    kwargs = {
        'perm': next_bit_for(bits, 'get_permission'),
        'user': next_bit_for(bits, 'for'),
        'objs': next_bit_for(bits, 'and'),
        'var_name': next_bit_for(bits, 'as', '"permission"'),
    }
    return PermissionForObjectNode(**kwargs)


@register.inclusion_tag('authority/permission_request_delete_link.html', takes_context=True)
def permission_request_delete_link(context, perm):
    """
    Renders a html link to the delete view of the given permission request. 
    Returns no content if the request-user has no permission to delete foreign
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        if user.has_perm('authority.delete_permission'):
            return _base_link(context, perm, 'authority-delete-request')
    return {'url': None}


@register.inclusion_tag('authority/permission_request_approve_link.html', takes_context=True)
def permission_request_approve_link(context, perm):
    """
    Renders a html link to the approve view of the given permission request. 
    Returns no content if the request-user has no permission to delete foreign
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        if user.has_perm('authority.approve_permission_request'):
            return _base_link(context, perm, 'authority-approve-request')
    return {'url': None}