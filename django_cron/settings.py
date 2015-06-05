'''
Simple helper to handle settings and their defaults.
'''

import warnings

from django.conf import settings


DEFAULTS = {
    'LOCK_BACKEND': 'django_cron.backends.lock.cache.CacheLock',
    'LOCKFILE_PATH': '/tmp',
    'LOCK_TIME': 24 * 60 * 60,  # 24 hours
    'CACHE': 'default',
    'EMAIL_PREFIX': '',
}


def setting(name):
    if name == 'CACHE' and hasattr(settings, 'CRON_CACHE'):
        warnings.warn(
            'CRON_CACHE setting was renamed '
            'into DJANGO_CRON_CACHE.',
            DeprecationWarning
        )
        return settings.CRON_CACHE

    if name == 'EMAIL_PREFIX' and hasattr(settings, 'FAILED_RUNS_CRONJOB_EMAIL_PREFIX'):
        warnings.warn(
            'FAILED_RUNS_CRONJOB_EMAIL_PREFIX setting was '
            'renamed into DJANGO_CRON_EMAIL_PREFIX',
            PendingDeprecationWarning
        )
        return settings.FAILED_RUNS_CRONJOB_EMAIL_PREFIX

    return getattr(
        settings,
        'DJANGO_CRON_{}'.format(name),
        DEFAULTS[name]
    )
