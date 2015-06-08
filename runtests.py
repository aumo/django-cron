#!/usr/bin/env python

# This file mainly exists to allow python setup.py test to work.
# flake8: noqa
import os
import sys

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_sqllite'

test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

import django
from django.test.utils import get_runner
from django.conf import settings


def runtests():
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=False)
    if hasattr(django, 'setup'):
        django.setup()

    test_label = 'django_cron'

    if sys.argv[0] != 'setup.py' and len(sys.args) > 1:
        test_label = '{}.tests.TestCase.{}'.format(test_label, sys.argv[1])

    failures = test_runner.run_tests([test_label])
    sys.exit(bool(failures))


if __name__ == '__main__':
    runtests()
