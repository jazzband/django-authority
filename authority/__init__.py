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

    from authority import utils
    utils.autodiscover_modules()
