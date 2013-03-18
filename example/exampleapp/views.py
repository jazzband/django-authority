from __future__ import print_function

from django.contrib.flatpages.views import flatpage
from django.contrib.flatpages.models import FlatPage

from authority.decorators import permission_required, permission_required_or_403

# @permission_required('flatpage_permission.top_secret',
#     (FlatPage, 'url__contains', 'url'), (FlatPage, 'url__contains', 'lala'))
# use this to return a 403 page:
@permission_required_or_403('flatpage_permission.top_secret',
    (FlatPage, 'url__contains', 'url'), 'lala')
def top_secret(request, url, lala=None):
    """
    A wrapping view that performs the permission check given in the decorator
    """
    print("secret!")
    return flatpage(request, url)
