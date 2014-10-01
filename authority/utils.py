from django.conf import settings
from django.contrib import auth


def get_user_class():
    if hasattr(settings, "AUTH_USER_MODEL"):
        return settings.AUTH_USER_MODEL
    elif hasattr(auth, "get_user_model"):
        return auth.get_user_model()
    else:
        return auth.models.User


User = get_user_class()