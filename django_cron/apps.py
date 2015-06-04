from django import apps
from django.core.checks import register

from django_cron.checks import check_crons


class AppConfig(apps.AppConfig):
    name = 'django_cron'

    def ready(self):
        register(check_crons)
