from optparse import make_option
import traceback

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.module_loading import import_string
try:
    from django.db import close_old_connections as close_connection
except ImportError:
    from django.db import close_connection


DEFAULT_LOCK_TIME = 24 * 60 * 60  # 24 hours


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--force', action='store_true', help='Force cron runs'),
        make_option('--silent', action='store_true', help='Do not push any message on console'),
    )

    def handle(self, *args, **options):
        """
        Iterates over all the CRON_CLASSES (or if passed in as a commandline argument)
        and runs them.
        """
        if args:
            cron_class_names = args
        else:
            cron_class_names = getattr(settings, 'CRON_CLASSES', [])

        try:
            crons_to_run = [import_string(x) for x in cron_class_names]
        except:
            error = traceback.format_exc()
            self.stdout.write('Make sure these are valid cron class names: %s\n%s' % (cron_class_names, error))
            return

        for cron_class in crons_to_run:
            cron_class().run(options['force'], options['silent'])
        close_connection()
