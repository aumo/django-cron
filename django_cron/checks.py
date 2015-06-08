from collections import defaultdict

from django.conf import settings
from django.core.checks import Error
from django.utils.module_loading import import_string
from django.utils.six import string_types

from django_cron import CronJobBase


def check_cron(cron_class_string, cron_job_codes):
    # The cron_job_codes dict is passed around
    # in order to register the encountered codes
    # and check for duplicates later on, it does not
    # feel very clean, maybe refactor OO style to avoid
    # this.
    try:
        cron_class = import_string(cron_class_string)
    except ImportError:
        return [Error(
            'Could not import a CronJob',
            hint=None,
            obj=cron_class_string,
            id='django_cron.E001'
        )]

    errors = []

    if not issubclass(cron_class, CronJobBase):
        errors.append(Error(
            'Classes defined in the CRON_CLASSES settings '
            'must be subclasses of CronJobBase',
            hint=None,
            obj=cron_class_string,
            id='django_cron.E002'
        ))

    if not hasattr(cron_class, 'code'):
        errors.append(Error(
            'CronJobBase subclasses must define a code'
            'attribute',
            hint=None,
            obj=cron_class_string,
            id='django_cron.E003'
        ))
    else:
        code = getattr(cron_class, 'code')
        if not isinstance(code, string_types):
            errors.append(Error(
                'CronJob codes must be of a string type',
                hint=None,
                obj=cron_class_string,
                id='django_cron.E004'
            ))
        else:
            cron_job_codes[code].append(cron_class_string)

    if not hasattr(cron_class, 'schedule'):
        errors.append(Error(
            'CronJobBase subclasses must define a schedule'
            'attribute',
            hint=None,
            obj=cron_class_string,
            id='django_cron.E005'
        ))
    else:
        schedule = getattr(cron_class, 'schedule', None)
        should_run_now = getattr(schedule, 'should_run_now', None)
        if not hasattr(should_run_now, '__call__'):
            errors.append(Error(
                'Schedules must define a should_run_now method',
                hint=None,
                obj=cron_class_string,
                id='django_cron.E006'
            ))

    do = getattr(cron_class, 'do', None)
    if not hasattr(do, '__call__'):
        errors.append(Error(
            'CronJobBase subclasses must define a do method',
            hint=None,
            obj=cron_class_string,
            id='django_cron.E007'
        ))

    return errors


def check_crons(app_configs, **kwargs):
    errors = []

    cron_classes = getattr(settings, 'CRON_CLASSES', [])

    cron_job_codes = defaultdict(list)
    for cron_class_string in cron_classes:
        cron_errors = check_cron(cron_class_string, cron_job_codes)
        if cron_errors:
            errors.extend(cron_errors)

    # Check for duplicate code:
    for code, cron_classes in cron_job_codes.items():
        if len(cron_classes) > 1:
            errors.append(Error(
                'CronJob codes must be unique',
                hint='Those classes define the '
                'same code({}): {}'.format(code, cron_classes),
                obj=cron_class_string,
                id='django_cron.E008'
            ))

    return errors
