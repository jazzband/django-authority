from django import template
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User, AnonymousUser

from authority import permissions
from authority.models import Permission
from authority.views import add_url_for_obj
from authority.forms import UserPermissionForm

register = template.Library()

class ComparisonNode(template.Node):
    """
    Implements a node to provide an "if user/group has permission on object"
    """
    def __init__(self, user, permission, nodelist_true, nodelist_false, *objs):
        self.user = user
        self.objs = objs
        # poll_permission.can_change
        self.perm = permission.strip('"')
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false

    def render(self, context):
        try:
            user = template.Variable(self.user).resolve(context)
            if self.objs:
                objs = []
                for obj in self.objs:
                    if obj is not None:
                        objs.append(
                            template.Variable(obj).resolve(context))
            else:
                objs = None
            check = permissions.registry.get_check(user, self.perm)
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
    This function provides funcitonality for the 'ifhasperm' template tag

    {% ifhasperm [permission_label].[check_name] [user] [*objs] %}
        lalala
    {% else %}
        meh
    {% endifhasperm %}

    {% if hasperm poll_permission.can_change request.user %}
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
        if user.has_perm('delete_foreign_permissions') or user.pk == perm.creator.pk:
            return {
                'next': context['request'].build_absolute_uri(),
                'delete_url': reverse('authority-delete-permission', kwargs={
                    'permission_pk': perm.pk,
                })
            }
    return {'delete_url': None}

@register.inclusion_tag('authority/permission_form.html', takes_context=True)
def permission_form(context, obj, perm=None):
    """
    Renders an "add permissions" form

    {% permission_form [obj] add_lesson %}
    {% permission_form lesson add_lesson %}
    """
    user = context['request'].user
    if user.is_authenticated():
        if user.has_perm('authority.add_permission'):
            return {
                'form': UserPermissionForm(perm, obj, initial=dict(codename=perm)),
                'form_url': add_url_for_obj(obj),
                'next': context['request'].build_absolute_uri(),
            }
    return {'form': None}

class PermissionForObjectNode(template.Node):
    def __init__(self, obj, user, var_name):
        self.obj = obj
        self.user = user
        self.var_name = var_name

    def resolve(self, var, context):
        """Resolves a variable out of context if it's not in quotes"""
        if var is None:
            return var
        if var[0] in ('"', "'") and var[-1] == var[0]:
            return var[1:-1]
        else:
            return template.Variable(var).resolve(context)

    def render(self, context):
        obj = self.resolve(self.obj, context)
        var_name = self.resolve(self.var_name, context)
        user = self.resolve(self.user, context)
        perms = []
        if not isinstance(user, AnonymousUser):
            perms = Permission.objects.for_object(obj)
            if isinstance(user, User):
                perms = perms.filter(user=user)
        context[var_name] = perms
        return ''

@register.tag
def get_permissions(parser, token):
    """
    Syntax::

        {% get_permissions obj %}
        {% for perm in permissions %}
            {{ perm }}
        {% endfor %}

        {% get_permissions obj as "my_permissions" %}
        {% get_permissions obj for request.user as "my_permissions" %}

    """
    def next_bit_for(bits, key, if_none=None):
        try:
            return bits[bits.index(key)+1]
        except ValueError:
            return if_none

    bits = token.contents.split()
    kwargs = {
        'obj': next_bit_for(bits, 'get_permissions'),
        'user': next_bit_for(bits, 'for'),
        'var_name': next_bit_for(bits, 'as', '"permissions"'),
    }
    return PermissionForObjectNode(**kwargs)
