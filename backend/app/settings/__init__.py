from importlib import import_module

from app.settings import conf

settings = import_module("app.settings.env." + conf.ENV_ID)
