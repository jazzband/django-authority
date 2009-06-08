from inspect import isfunction, getmembers
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured

LOADING = False

def autodiscover():
    """
    Goes and imports the permissions submodule of every app in INSTALLED_APPS
    to make sure the permission set classes are registered correctly.
    """
    global LOADING
    if LOADING:
        return
    LOADING = True

    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        print "checking %s" % app
        try:
            app_path = import_module(app).__path__
        except AttributeError:
            continue
        try:
            imp.find_module('permissions', app_path)
        except ImportError:
            continue
        import_module("%s.permissions" % app)
    LOADING = False
