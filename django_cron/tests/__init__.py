import threading
from time import sleep
from datetime import timedelta

from django import db
from django.apps import apps
from django.utils import unittest
from django.core import checks
from django.core.management import call_command
from django.test.utils import override_settings
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from freezegun import freeze_time

from django_cron.helpers import humanize_duration
from django_cron.models import CronJobLog
from django_cron.settings import setting


class OutBuffer(object):
    content = []
    modified = False
    _str_cache = ''

    def write(self, *args):
        self.content.extend(args)
        self.modified = True

    def str_content(self):
        if self.modified:
            self._str_cache = ''.join((str(x) for x in self.content))
            self.modified = False

        return self._str_cache


class TestCase(unittest.TestCase):

    success_cron = 'django_cron.tests.cron.TestSucessCronJob'
    error_cron = 'django_cron.tests.cron.TestErrorCronJob'
    five_mins_cron = 'django_cron.tests.cron.Test5minsCronJob'
    legacy_five_mins_cron = 'django_cron.tests.cron.LegacyTest5minsCronJob'
    run_at_times_cron = 'django_cron.tests.cron.TestRunAtTimesCronJob'
    legacy_run_at_times_cron = 'django_cron.tests.cron.LegacyTestRunAtTimesCronJob'
    wait_3sec_cron = 'django_cron.tests.cron.Wait3secCronJob'
    does_not_exist_cron = 'ThisCronObviouslyDoesntExist'
    test_failed_runs_notification_cron = 'django_cron.cron.FailedRunsNotificationCronJob'
    test_does_not_subclass_cron = 'django_cron.tests.cron.DoesNotSubclassCronJobBase'
    test_no_code_cron = 'django_cron.tests.cron.NoCodeCronJob'
    test_code_no_string_cron = 'django_cron.tests.cron.CodeNotStringCronJob'
    test_no_schedule_cron = 'django_cron.tests.cron.NoScheduleCronJob'
    test_invalid_schedule_cron = 'django_cron.tests.cron.InvalidScheduleCronJob'
    test_no_do_cron = 'django_cron.tests.cron.NoDoCronJob'
    test_duplicate_code_cron_1 = 'django_cron.tests.cron.DuplicateCodeCronJob1'
    test_duplicate_code_cron_2 = 'django_cron.tests.cron.DuplicateCodeCronJob2'
    test_day_of_week_job = 'django_cron.tests.cron.DayOfWeekCronJob'

    def setUp(self):
        CronJobLog.objects.all().delete()

    def test_success_cron(self):
        call_command('runcrons', self.success_cron, force=True)
        self.assertEqual(CronJobLog.objects.filter(is_success=True).count(), 1)

    def test_failed_cron(self):
        call_command('runcrons', self.error_cron, force=True)
        self.assertEqual(CronJobLog.objects.filter(is_success=False).count(), 1)

    def test_not_exists_cron(self):
        out_buffer = OutBuffer()
        call_command('runcrons', self.does_not_exist_cron, force=True, stdout=out_buffer)

        self.assertIn('Make sure these are valid cron class names', out_buffer.str_content())
        self.assertIn(self.does_not_exist_cron, out_buffer.str_content())
        self.assertEqual(CronJobLog.objects.all().count(), 0)

    @override_settings(DJANGO_CRON_LOCK_BACKEND='django_cron.backends.lock.file.FileLock')
    def test_file_locking_backend(self):
        call_command('runcrons', self.success_cron, force=True)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

    def _test_runs_every_mins(self, cron_class):
        with freeze_time("2014-01-01 00:00:00"):
            call_command('runcrons', cron_class)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        with freeze_time("2014-01-01 00:04:59"):
            call_command('runcrons', cron_class)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        with freeze_time("2014-01-01 00:05:01"):
            call_command('runcrons', cron_class)
        self.assertEqual(CronJobLog.objects.all().count(), 2)

    def test_runs_every_mins(self):
        self._test_runs_every_mins(self.five_mins_cron)

    def test_legacy_runs_every_mins(self):
        self._test_runs_every_mins(self.legacy_five_mins_cron)

    def _test_runs_at_time(self, cron_class):
        with freeze_time("2014-01-01 00:00:01"):
            call_command('runcrons', cron_class)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        with freeze_time("2014-01-01 00:04:50"):
            call_command('runcrons', self.run_at_times_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        with freeze_time("2014-01-01 00:05:01"):
            call_command('runcrons', self.run_at_times_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 2)

        with freeze_time("2014-01-01 00:05:30"):
            call_command('runcrons', self.run_at_times_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 2)

        with freeze_time("2014-01-02 00:00:01"):
            call_command('runcrons', self.run_at_times_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 3)

    def test_runs_at_time(self):
        self._test_runs_at_time(self.run_at_times_cron)

    def test_legacy_runs_at_time(self):
        self._test_runs_at_time(self.legacy_run_at_times_cron)

    def test_admin(self):
        password = 'test'
        user = User.objects.create_superuser(
            'test',
            'test@tivix.com',
            password
        )
        self.client = Client()
        self.client.login(username=user.username, password=password)

        # get list of CronJobLogs
        url = reverse('admin:django_cron_cronjoblog_changelist')

        # edit CronJobLog object
        call_command('runcrons', self.success_cron, force=True)
        log = CronJobLog.objects.all()[0]
        url = reverse('admin:django_cron_cronjoblog_change', args=(log.id,))
        response = self.client.get(url)
        self.assertIn('Cron job logs', str(response.content))

    def run_cronjob_in_thread(self, logs_count):
        call_command('runcrons', self.wait_3sec_cron)
        self.assertEqual(CronJobLog.objects.all().count(), logs_count + 1)
        db.close_old_connections()

    def test_cache_locking_backend(self):
        """
        with cache locking backend
        """
        t = threading.Thread(target=self.run_cronjob_in_thread, args=(0, ))
        t.daemon = True
        t.start()
        # this shouldn't get running
        sleep(0.1)  # to avoid race condition
        call_command('runcrons', self.wait_3sec_cron)
        t.join(10)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

    # TODO: this test doesn't pass - seems that second cronjob is locking file
    # however it should throw an exception that file is locked by other cronjob
    # @override_settings(
    #     DJANGO_CRON_LOCK_BACKEND='django_cron.backends.lock.file.FileLock',
    #     DJANGO_CRON_LOCKFILE_PATH=os.path.join(os.getcwd())
    # )
    # def test_file_locking_backend_in_thread(self):
    #     """
    #     with file locking backend
    #     """
    #     logs_count = CronJobLog.objects.all().count()
    #     t = threading.Thread(target=self.run_cronjob_in_thread, args=(logs_count,))
    #     t.daemon = True
    #     t.start()
    #     # this shouldn't get running
    #     sleep(1)  # to avoid race condition
    #     call_command('runcrons', self.wait_3sec_cron)
    #     t.join(10)
    #     self.assertEqual(CronJobLog.objects.all().count(), logs_count + 1)

    def test_failed_runs_notification(self):
        for i in range(10):
            call_command('runcrons', self.error_cron, force=True)
        call_command('runcrons', self.test_failed_runs_notification_cron)

        self.assertEqual(CronJobLog.objects.all().count(), 11)

    def test_humanize_duration(self):
        test_subjects = (
            (timedelta(days=1, hours=1, minutes=1, seconds=1), '1 day, 1 hour, 1 minute, 1 second'),
            (timedelta(days=2), '2 days'),
            (timedelta(days=15, minutes=4), '15 days, 4 minutes'),
            (timedelta(), '< 1 second'),
        )

        for duration, humanized in test_subjects:
            self.assertEqual(
                humanize_duration(duration),
                humanized
            )

    @override_settings(CRON_CLASSES=[
        does_not_exist_cron,
        test_does_not_subclass_cron,
        test_no_code_cron,
        test_code_no_string_cron,
        test_no_schedule_cron,
        test_invalid_schedule_cron,
        test_no_do_cron,
        test_duplicate_code_cron_1,
        test_duplicate_code_cron_2,
    ])
    def test_system_checks(self):
        app_config = apps.get_app_config('django_cron')
        issues = checks.run_checks(app_configs=[app_config])

        issues_ids = [issue.id for issue in issues]

        assert 'django_cron.E001' in issues_ids
        assert 'django_cron.E002' in issues_ids
        assert 'django_cron.E003' in issues_ids
        assert 'django_cron.E004' in issues_ids
        assert 'django_cron.E005' in issues_ids
        assert 'django_cron.E006' in issues_ids
        assert 'django_cron.E007' in issues_ids
        assert 'django_cron.E008' in issues_ids

    def test_day_of_week_schedule(self):
        # Freeze time on a monday.
        with freeze_time("2015-06-01 00:00:00"):
            call_command('runcrons', self.test_day_of_week_job)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        # And now, not a monday.
        with freeze_time("2015-06-02 00:00:00"):
            call_command('runcrons', self.test_day_of_week_job)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

    @override_settings(
        CRON_CACHE='cron_cache',
        FAILED_RUNS_CRONJOB_EMAIL_PREFIX='email_prefix'
    )
    def test_setting(self):
        self.assertEqual(setting('CACHE'), 'cron_cache')
        self.assertEqual(setting('EMAIL_PREFIX'), 'email_prefix')
