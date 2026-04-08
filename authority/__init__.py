from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("django-authority")
except PackageNotFoundError:
    # package is not installed
    pass

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

    from django.utils.module_loading import autodiscover_modules

    autodiscover_modules("permissions")
