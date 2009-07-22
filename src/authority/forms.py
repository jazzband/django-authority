from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django.forms.util import ErrorList

from authority import permissions, get_choices_for
from authority.models import Permission

class BasePermissionForm(forms.ModelForm):
    codename = forms.CharField(label=_('Permission'))

    class Meta:
        model = Permission

    def __init__(self, perm=None, obj=None, approved=False, *args, **kwargs):
        self.perm = perm
        self.obj = obj
        self.approved = approved
        if not self.approved:
            self.base_fields['user'].widget = forms.HiddenInput()
        else:
            self.base_fields['user'].widget = forms.TextInput()
        if obj and perm:
            self.base_fields['codename'].widget = forms.HiddenInput()
        elif obj and not perm:
            perm_choices = get_choices_for(self.obj)
            self.base_fields['codename'].widget = forms.Select(
                choices=perm_choices)
        super(BasePermissionForm, self).__init__(*args, **kwargs)

    def save(self, request, commit=True, *args, **kwargs):
        if not self.approved:
            self.instance.user = request.user
        self.instance.creator = request.user
        self.instance.content_type = ContentType.objects.get_for_model(self.obj)
        self.instance.object_id = self.obj.id
        self.instance.codename = self.perm
        self.instance.approved = self.approved
        return super(BasePermissionForm, self).save(commit)


class UserPermissionForm(BasePermissionForm):
    user = forms.CharField(label=_('User'))

    class Meta(BasePermissionForm.Meta):
        fields = ('user',)

    def clean(self):
        cleaned_data = self.cleaned_data
        user = self.cleaned_data.get("user", None)
        if user:
            try:
                user = User.objects.get(username__iexact=user)
            except User.DoesNotExist:
                raise forms.ValidationError(
                    _("A user with that username does not exist."))
            check = permissions.BasePermission(user=user)
            error_msg = None
            if user.is_superuser:
                error_msg = _("The user %(user)s do not need to request " \
                              "access to any permission as it is a super user.")
            elif check.has_perm(self.perm, self.obj):
                error_msg = _("The user %(user)s already has the permission " \
                              "'%(perm)s' for %(object_name)s '%(obj)s'")
            elif check.has_request(self.perm, self.obj):
                error_msg = _("The user %(user)s already has a permission " \
                              "request '%(perm)s' for %(object_name)s '%(obj)s'")

            if error_msg:
                msg = error_msg % {
                        'object_name': self.obj._meta.object_name.lower(),
                        'perm': self.perm,
                        'obj': self.obj,
                        'user': user,
                    }
                # Only display the error for the user field when it is not hidden
                if self.approved:
                    self._errors["user"] = ErrorList([msg])
                else:
                    raise forms.ValidationError(msg)
            cleaned_data['user'] = user

        return cleaned_data


class GroupPermissionForm(BasePermissionForm):
    group = forms.CharField(label=_('Group'))

    class Meta(BasePermissionForm.Meta):
        fields = ('group',)

    def clean_group(self):
        groupname = self.cleaned_data["group"]
        try:
            group = Group.objects.get(name__iexact=groupname)
        except Group.DoesNotExist:
            raise forms.ValidationError(
                _("A group with that name does not exist."))
        check = permissions.BasePermission(group=group)
        if check.has_perm(self.perm, self.obj):
            raise forms.ValidationError(
                _("This group already has the permission '%(perm)s' for %(object_name)s '%(obj)s'") % {
                    'perm': self.perm,
                    'object_name': self.obj._meta.object_name.lower(),
                    'obj': self.obj,
                })
        return group
