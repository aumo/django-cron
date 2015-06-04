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
}


def setting(name):
    if name == 'CACHE' and hasattr(settings, 'CRON_CACHE'):
        warnings.warn("CRON_CACHE setting was renamed into DJANGO_CRON_CACHE.",
                      DeprecationWarning)
        return settings.cache

    return getattr(
        settings,
        'DJANGO_CRON_{}'.format(name),
        DEFAULTS[name]
    )
