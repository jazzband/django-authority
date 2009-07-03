from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group

from authority.models import Permission
from authority import permissions

class BasePermissionForm(forms.ModelForm):
    codename = forms.CharField(label=_('Permission'))

    class Meta:
        model = Permission

    def __init__(self, perm=None, obj=None, *args, **kwargs):
        self.perm = perm
        self.obj = obj
        if obj and perm:
            self.base_fields['codename'].widget = forms.HiddenInput()
        elif obj and not perm:
            perm_choices = permissions.registry.get_choices_for(self.obj)
            self.base_fields['codename'].widget = forms.Select(choices=perm_choices)
        super(BasePermissionForm, self).__init__(*args, **kwargs)

    def save(self, request, commit=True, *args, **kwargs):
        self.instance.creator = request.user
        self.instance.content_type = ContentType.objects.get_for_model(self.obj)
        self.instance.object_id = self.obj.id
        self.instance.codename = self.perm
        return super(BasePermissionForm, self).save(commit)

class UserPermissionForm(BasePermissionForm):
    user = forms.CharField(label=_('User'))

    class Meta(BasePermissionForm.Meta):
        fields = ('user',)

    def clean_user(self):
        username = self.cleaned_data["user"]
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise forms.ValidationError(
                _("A user with that username does not exist."))
        check = permissions.BasePermission(user=user)
        if check.has_perm(self.perm, self.obj):
            raise forms.ValidationError(
                _("This user already has the permission '%(perm)s' for %(object_name)s '%(obj)s'") % {
                    'perm': self.perm,
                    'object_name': self.obj._meta.object_name.lower(),
                    'obj': self.obj,
                })
        return user

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
