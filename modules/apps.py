""" Django app config
"""
from django.apps import AppConfig


class ModulesConfig(AppConfig):
    """ Amsterdam App Api Configuration """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules'
