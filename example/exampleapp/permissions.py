from django.contrib.flatpages.models import FlatPage
from django.utils.translation import ugettext_lazy as _

from authority import permissions

class FlatPagePermissionSet(permissions.BasePermission):
    model = FlatPage
    label = 'flatpage_permission'
    checks = ('top_secret',)

    def top_secret(self, flatpage=None):
        if flatpage and flatpage.registration_required:
            return self.can_browse(obj=flatpage)
        return False
    top_secret.verbose_name=_('Is allowed to see top secret flatpages')
