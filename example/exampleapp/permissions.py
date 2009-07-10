from django.contrib.flatpages.models import FlatPage
from django.utils.translation import ugettext_lazy as _

import authority
from authority.permissions import BasePermission

class FlatPagePermission(BasePermission):
    """
    This class contains a bunch of checks:
    
    1. the default checks 'add_flatpage', 'browse_flatpage',
       'change_flatpage' and 'delete_flatpage'
    2. the custom checks:
        a) 'review_flatpage', which is similar to the default checks
        b) 'top_secret', which is represented by the top_secret method

    You can use those checks in your views directly like::

        def review_flatpage(request, url):
            flatpage = get_object_or_404(url__contains=url)
            check = FlatPagePermission(request.user)
            if check.review_flatpage(obj=flatpage):
                print "yay, you can review this flatpage!"
            return flatpage(request, url)

    Or the same view using the decorator permission_required::

        @permission_required('flatpage_permission.review_flatpage',
            ('flatpages.flatpage', 'url__contains', 'url'))
        def review_flatpage(request, url):
            print "yay, you can review this flatpage!"
            return flatpage(request, url)

    Or you can use this permission in your templates like this::

        {% ifhasperm "flatpage_permission.review_flatpage" request.user flatpage %}
            Yes, you are allowed to review flatpage '{{ flatpage }}', aren't you?
        {% else %}
            Nope, sorry. You aren't allowed to review this flatpage.
        {% endifhasperm %}

    """
    label = 'flatpage_permission'
    checks = ('review', 'top_secret')

    def top_secret(self, flatpage=None, lala=None):
        if flatpage and flatpage.registration_required:
            return self.browse_flatpage(obj=flatpage)
        return False
    top_secret.short_description=_('Is allowed to see top secret flatpages')

authority.register(FlatPage, FlatPagePermission)
