INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.humanize',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',

    'django_cron',
]

SECRET_KEY = "wknfgl34qtnjo&Yk3jqfjtn2k3jtnk4wtnk"


CRON_CLASSES = [
    'django_cron.tests.cron.TestSucessCronJob',
    'django_cron.tests.cron.TestErrorCronJob',
    'django_cron.tests.cron.Test5minsCronJob',
    'django_cron.tests.cron.TestRunAtTimesCronJob',
    'django_cron.tests.cron.Wait3secCronJob',
    'django_cron.cron.FailedRunsNotificationCronJob'
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware'
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
    },
    'loggers': {
        'django_cron': {
            'handlers': ['null'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': 'django_cache',
    }
}

ROOT_URLCONF = 'test_urls'
SITE_ID = 1
STATIC_URL = '/static/'
