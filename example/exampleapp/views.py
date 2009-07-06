from django.contrib.flatpages.views import flatpage
from django.contrib.flatpages.models import FlatPage

from authority.decorators import permission_required, permission_required_or_403

# @permission_required_or_403('flatpage_permission.top_secret', { # use this to return a 403 page
#     'url': (FlatPage, 'url__contains'), 'lala': (FlatPage, 'url__contains')})
@permission_required('flatpage_permission.top_secret', {
    'url': (FlatPage, 'url__contains'), 'lala': (FlatPage, 'url__contains')})
def top_secret(request, url, lala=None):
    """
    A wrapping view that performs the permission check given in the decorator
    """
    print "secret!"
    return flatpage(request, url)
