from django.contrib.flatpages.models import FlatPage
from django.utils.translation import ugettext_lazy as _

from authority import permissions

class FlatPagePermission(permissions.BasePermission):
    """
    This class contains a bunch of default and one custom permission check.
    You can use the default checks can_add, can_browse, can_change and
    can_delete to assemble your own. They can later be checked against from
    your views directly or templates with the ifhasperm template tag.
    """
    model = FlatPage
    label = 'flatpage_permission'
    checks = ('top_secret',)

    def top_secret(self, flatpage=None):
        if flatpage and flatpage.registration_required:
            return self.can_browse(obj=flatpage)
        return False
    top_secret.verbose_name=_('Is allowed to see top secret flatpages')
