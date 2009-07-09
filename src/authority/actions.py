from django import forms, template
from django.contrib.admin import helpers, site
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.contrib.contenttypes.models import ContentType
from django.forms.formsets import all_valid

try:
    from django.contrib.admin import actions
except ImportError:
    actions = False

from authority.admin import PermissionInline

class ActionPermissionInline(PermissionInline):
    raw_id_fields = ()
    template = 'admin/edit_inline/action_tabular.html'

class ActionErrorList(forms.util.ErrorList):
    def __init__(self, inline_formsets):
        for inline_formset in inline_formsets:
            self.extend(inline_formset.non_form_errors())
            for errors_in_inline_form in inline_formset.errors:
                self.extend(errors_in_inline_form.values())

def edit_permissions(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    app_label = opts.app_label
    inline = ActionPermissionInline(queryset.model, modeladmin.admin_site)
    formsets = []
    for obj in queryset:
        prefixes = {}
        FormSet = inline.get_formset(request, obj)
        prefix = "%s-%s" % (FormSet.get_default_prefix(), obj.pk)
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
        if prefixes[prefix] != 1:
            prefix = "%s-%s-%s" % (prefix, prefixes[prefix])
        if request.POST.get('post'):
            formset = FormSet(data=request.POST, files=request.FILES,
                              instance=obj, prefix=prefix)
        else:
            formset = FormSet(instance=obj, prefix=prefix)
        formsets.append(formset)

    media = modeladmin.media
    inline_admin_formsets = []
    for formset in formsets:
        fieldsets = list(inline.get_fieldsets(request))
        inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets)
        inline_admin_formsets.append(inline_admin_formset)
        media = media + inline_admin_formset.media

    ordered_objects = opts.get_ordered_objects()
    if request.POST.get('post'):
        if all_valid(formsets):
            for formset in formsets:
                formset.save()
        return None

    context = {
        'errors': ActionErrorList(formsets),
        'title': ugettext('Permissions for %s') % force_unicode(opts.verbose_name_plural),
        'inline_admin_formsets': inline_admin_formsets,
        'root_path': modeladmin.admin_site.root_path,
        'app_label': app_label,
        'change': True,
        'ordered_objects': ordered_objects,
        'form_url': mark_safe(''),
        'opts': opts,
        'target_opts': queryset.model._meta,
        'content_type_id': ContentType.objects.get_for_model(queryset.model).id,
        'save_as': False,
        'save_on_top': False,
        'is_popup': False,
        'media': mark_safe(media),
        'show_delete': False,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'queryset': queryset,
        "object_name": force_unicode(opts.verbose_name),
    }
    template_name = getattr(modeladmin, 'permission_change_form_template', [
        "admin/%s/%s/permission_change_form.html" % (app_label, opts.object_name.lower()),
        "admin/%s/permission_change_form.html" % app_label,
        "admin/permission_change_form.html"
    ])
    return render_to_response(template_name, context,
                              context_instance=template.RequestContext(request))
edit_permissions.short_description = ugettext("Permissions for selected %(verbose_name_plural)s")

if actions:
    site.add_action(edit_permissions)
