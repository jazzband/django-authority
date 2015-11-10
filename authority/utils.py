import django
from django.conf import settings
from django.contrib import auth


def get_user_class():
    """
    Returns the User model class. In Django 1.7 and above, get_user_model()
    internally uses the App Registry, which may not be queried until it is ready.
    We can break this cycle via indirection by returning a string instead.
    """
    if django.VERSION[:2] >= (1, 7):
        return settings.AUTH_USER_MODEL
    elif hasattr(auth, "get_user_model"):
        return auth.get_user_model()
    else:
        return auth.models.User


User = get_user_class()