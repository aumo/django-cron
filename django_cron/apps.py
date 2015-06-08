from django import apps
from django.core.checks import register

from django_cron.checks import check_crons


class AppConfig(apps.AppConfig):
    name = 'django_cron'

    def ready(self):
        # register in Django 1.7 works as a decorator only.
        # When support for Django 1.7 is not needed anymore,
        # use register(check_crons). COMPAT_1.7
        register()(check_crons)
