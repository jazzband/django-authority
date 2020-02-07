from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution("django-authority").version
except DistributionNotFound:
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
