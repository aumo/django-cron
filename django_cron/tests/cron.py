from time import sleep

from django_cron import CronJobBase, Fixed, Periodic, Schedule


class DoNothingJob(CronJobBase):
    def do(self):
        pass


class TestSuccessCronJob(DoNothingJob):
    code = 'test_success_cron_job'
    schedule = Periodic(minutes=0)

    def do(self):
        pass


class TestSuccessParallelCronJob(TestSuccessCronJob):
    ALLOW_PARALLEL_RUNS = True


class TestErrorCronJob(CronJobBase):
    code = 'test_error_cron_job'
    schedule = Periodic(minutes=0)


class Test5minsCronJob(DoNothingJob):
    code = 'test_run_every_mins'
    schedule = Periodic(minutes=5)


class TestRetry5minsCronJob(Test5minsCronJob):
    code = 'test_retry_run_every_mins'
    schedule = Periodic(minutes=5, retry_delay_minutes=2)


class LegacyTest5minsCronJob(DoNothingJob):
    code = 'legacy_test_run_every_mins'
    schedule = Schedule(run_every_mins=5)


class TestRunAtTimesCronJob(DoNothingJob):
    code = 'test_run_at_times'
    schedule = Fixed(times=['0:00', '0:05'])


class LegacyTestRunAtTimesCronJob(DoNothingJob):
    code = 'test_run_at_times'
    schedule = Schedule(run_at_times=['0:00', '0:05'])


class WaitCronJob(CronJobBase):
    code = 'test_wait_seconds'
    schedule = Periodic(minutes=5)

    def do(self):
        sleep(.4)


class DoesNotSubclassCronJobBase(object):
    code = 'test_does_not_subclass'
    schedule = Periodic(minutes=5)

    def do(self):
        pass


class NoCodeCronJob(DoNothingJob):
    schedule = Periodic(minutes=5)


class CodeNotStringCronJob(DoNothingJob):
    code = 0
    schedule = Periodic(minutes=5)


class NoScheduleCronJob(DoNothingJob):
    code = 'test_no_schedule'


class InvalidScheduleCronJob(DoNothingJob):
    code = 'invalid_schedule'
    schedule = 'invalid'


class NoDoCronJob(CronJobBase):
    code = 'test_no_do'
    schedule = Schedule(run_every_mins=5)


class DuplicateCodeCronJob1(DoNothingJob):
    code = 'duplicate code'
    schedule = Periodic(minutes=5)


class DuplicateCodeCronJob2(DuplicateCodeCronJob1):
    pass


class DayOfWeekCronJob(DoNothingJob):
    code = 'day of week'
    schedule = Fixed(times=['00:00'], days_of_week=[0, ])
