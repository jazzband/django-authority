from django.contrib.flatpages.models import FlatPage
from authority.permissions import BasePermission

class FlatPagePermission(BasePermission):
    model = FlatPage
    label = 'flatpage_permission'
