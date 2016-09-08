"""
    Wrappers for interacting with Django in the server.
"""
from django.apps import apps as django_apps

from .._caches import APP_FROM_APPNAME
from .application import DjangoApp

IMPORTING = None


def applications():
    """Return the Django application wrappers for all installed apps.
    """
    # We need the global or the tracking doesn't work
    # pylint: disable = global-statement
    if APP_FROM_APPNAME:
        return APP_FROM_APPNAME.values()
    else:
        apps = [get_application(app) for app in django_apps.get_app_configs()
                if any(app.get_models())]
        for app in apps:
            global IMPORTING
            IMPORTING = app.name
            __import__(app.name, globals(), locals(), ['slumber_server'])
            IMPORTING = None
        return apps


def get_application(app_config):
    """Build a Django application wrapper around an application given
    by its name.
    """
    if app_config.name not in APP_FROM_APPNAME:
        APP_FROM_APPNAME[app_config.name] = DjangoApp(app_config)
    return APP_FROM_APPNAME[app_config.name]
