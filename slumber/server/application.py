"""
    Implements the Django application wrapper for the Slumber server.
"""
from .model import DjangoModel


class DjangoApp(object):
    """Describes a Django application.
    """
    def __init__(self, app_config):
        self.app_config = app_config
        self.name = app_config.name
        self.path = app_config.name.replace('.', '/')
        self.module = app_config.module
        self.models = {}
        for model in app_config.get_models():
            model_wrap = DjangoModel(self, model)
            self.models[model.__name__] = model_wrap

    def __repr__(self):
        return self.name
