from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.db.models.loading import get_model
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext, ugettext_lazy as _
from django.template.context import RequestContext
from django.template import loader
from django.contrib.auth.decorators import login_required

from authority.models import Permission
from authority.forms import UserPermissionForm

def add_url_for_obj(obj):
    return reverse('authority-add-permission', kwargs={
            'app_label': obj._meta.app_label,
            'module_name': obj._meta.module_name,
            'pk': obj.pk})

@require_POST
@login_required
def add_permission(request, app_label, module_name, pk, extra_context={},
                   template_name='authority/permission_form.html'):
    next = request.POST.get('next', '/')
    codename = request.POST.get('codename', None)
    if codename is None:
        return HttpResponseForbidden(next)
    model = get_model(app_label, module_name)
    if model is None:
        return permission_denied(request)
    obj = get_object_or_404(model, pk=pk)
    form = UserPermissionForm(data=request.POST, obj=obj,
                              perm=codename, initial={'codename': codename})
    if form.is_valid():
        form.save(request)
        request.user.message_set.create(
            message=ugettext('You added a permission.'))
        return HttpResponseRedirect(next)
    else:
        context = {
            'form': form,
            'form_url': add_url_for_obj(obj),
            'next': next,
            'perm': codename,
        }
        context.update(extra_context)
        return render_to_response(template_name, context,
                                  context_instance=RequestContext(request))

@login_required
def delete_permission(request, permission_pk):
    permission = get_object_or_404(Permission, pk=permission_pk)
    if request.user.has_perm('delete_foreign_permissions') \
       or request.user == permission.creator:
        permission.delete()
        request.user.message_set.create(
            message=ugettext('You removed the permission.'))
    next = request.REQUEST.get('next') or '/'
    return HttpResponseRedirect(next)

def permission_denied(request, template_name=None, extra_context={}):
    """
    Default 403 handler.

    Templates: `403.html`
    Context:
        request_path
            The path of the requested URL (e.g., '/app/pages/bad_page/')
    """
    if template_name is None:
       template_name = ('403.html', 'authority/403.html')
    context = {
        'request_path': request.path,
    }
    context.update(extra_context)
    return HttpResponseForbidden(loader.render_to_string(template_name, context,
                                 context_instance=RequestContext(request)))
