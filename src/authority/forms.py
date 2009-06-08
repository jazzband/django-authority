from django import forms
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group

from authority.models import Permission
from authority.permissions import BasePermission

class BasePermissionForm(ModelForm):

    class Meta:
        model = Permission

    def __init__(self, perm=None, obj=None, *args, **kwargs):
        self.perm = perm
        self.obj = obj
        super(BasePermissionForm, self).__init__(*args, **kwargs)

    def save(self, request, commit=True, *args, **kwargs):
        self.instance.creator = request.user
        self.instance.content_type = ContentType.objects.get_for_model(self.obj)
        self.instance.object_id = self.obj.id
        self.instance.codename = self.perm
        return super(BasePermissionForm, self).save(commit)

class UserPermissionForm(BasePermissionForm):
    codename = forms.CharField(widget=forms.HiddenInput())
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
        check = BasePermission(user)
        if check.has_perm(self.perm, self.obj):
            raise forms.ValidationError(
                _("This user already has permission '%(perm)s' on %(obj)s") % {
                    'perm': self.perm,
                    'obj': self.obj
                })
        return user

class GroupPermissionForm(BasePermissionForm):
    name = forms.CharField(label=_('Group'))

    class Meta(BasePermissionForm.Meta):
        fields = ('group',)

    def clean_group(self):
        name = self.cleaned_data["name"]
        try:
            group = Group.objects.get(name__iexact=name)
        except Group.DoesNotExist:
            raise forms.ValidationError(
                _("A group with that name does not exist."))
        self.instance.group = group
        return name

    def save(self, request, commit=True):
        group=self.cleaned_data.get("group", None)
        check = BasePermission(group=group)
        if check.has_perm(self.perm, self.obj):
            raise forms.ValidationError(
                _("This group already has permission '%(perm)s' on %(obj)s") % {
                    'perm': self.perm,
                    'obj': self.obj,
                })
        self.instance.group = group
        return super(GroupPermissionForm, self).save(request, self.obj, commit)

    # def del_row_perm(self, instance, perm, check_groups=False,
    #                  fail_silently=False):
    #     """
    #     Remove granular permission perm from user on an object instance
    #     """
    #     if not self.has_row_perm(instance, perm, not check_groups):
    #         if not fail_silently:
    #             raise DoesNotHavePermission(self, perm, instance)
    #         else:
    #             return
    #     content_type = ContentType.objects.get_for_model(instance)
    #     objects = Permission.objects.filter(user=self,
    #                                         content_type__pk=content_type.id,
    #                                         object_id=instance.id, name=perm)
    #     objects.delete()
    # 
    # 
