import inspect
from decorator import decorator
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, HttpResponseRedirect, Http404
from django.utils.http import urlquote
from django.db.models import Model, get_model
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME

from authority import permissions

def permission_required(perm, *args, **kwargs):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    """
    login_url = kwargs.pop('login_url', None)
    if not login_url:
        login_url = getattr(settings, 'LOGIN_URL', '/')
    redirect_field_name = kwargs.pop('redirect_field_name', REDIRECT_FIELD_NAME)
    model_lookups = args
    def _permission_required(view_func, request, *args, **kwargs):
        objs = []
        # model_lookups = [('flatpages.flatpage', 'url__contains')]
        for i, arguments in enumerate(model_lookups):
            model, lookup = arguments
            if isinstance(model, basestring):
                model_class = get_model(*model.split("."))
            else:
                model_class = model
            if model_class is None:
                raise ValueError(
                    "The given argument '%s' is not a valid model." % model)
            if inspect.isclass(model_class) and \
                    not issubclass(model_class, Model):
                raise ValueError(
                    'The argument %s needs to be a model.' % model)
            objs.append(get_object_or_404(model_class, **{lookup: args[i]}))
        check = permissions.registry.get_check(request.user, perm)
        if check is not None:
            if check(*objs):
                return view_func(request, *args, **kwargs)
        #return HttpResponseForbidden("Permission")
        raise PermissionDenied()
    return decorator(_permission_required)
