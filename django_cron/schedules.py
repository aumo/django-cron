from datetime import datetime, time, timedelta
import warnings

from django.db.models import Q
from django.utils import timezone

from django_cron.models import CronJobLog


class BaseSchedule(object):
    '''
    Base class for Schedules.
    Does nothing at the moment, keep it in case
    it needs to in the future.
    '''
    pass


class RunEveryMinutes(BaseSchedule):
    '''
    Schedule class that allows a job to be run every X minutes.
    :param minutes: the interval in minutes between each run.
    :param retry_after_failure_mins: the interval before retrying a failed run.
    '''
    def __init__(self, minutes, retry_after_failure_mins=None):
        self.minutes = minutes
        self.retry_after_failure_mins = retry_after_failure_mins

    def should_run_now(self, cron_job):
        # We check last job - success or not
        if cron_job.last_job \
           and not cron_job.last_job.is_success \
           and self.retry_after_failure_mins:
            next_retry_time = cron_job.last_job.start_time + timedelta(minutes=self.retry_after_failure_mins)
            return timezone.now() > next_retry_time

        if cron_job.last_successful_job:
            next_run_time = cron_job.last_successful_job.start_time \
                + timedelta(minutes=self.minutes)
            return timezone.now() > next_run_time
        else:
            return True


class RunAtTimes(BaseSchedule):
    '''
    Schedule class that allows running a job at
    specific times each day.
    :param times: a list of strings representing the
    times the job must be run at, ex: `['10:00', '18:00']`
    '''
    def __init__(self, times):
        # Parse the times.
        self.times = [datetime.strptime(t, "%H:%M").time() for t in times]

    def should_run_now(self, cron_job):
        for scheduled_time in self.times:
            now = timezone.now()
            actual_time = now.time()
            if actual_time >= scheduled_time:
                similar_crons_that_ran_today = CronJobLog.objects.filter(
                    code=cron_job.code,
                    ran_at_time=scheduled_time,
                    is_success=True
                ).filter(
                    Q(start_time__gt=now) | Q(end_time__gte=datetime.combine(now.date(), time.min))
                )
                if not similar_crons_that_ran_today.exists():
                    cron_job.cron_log.ran_at_time = scheduled_time
                    return True


class Schedule(object):
    '''
    Only here for backward compatibility.
    Uses the right Schedule class depending
    on the parameters it was passed.
    '''
    def __init__(self, run_every_mins=None, run_at_times=None, retry_after_failure_mins=None):
        warnings.warn(
            'Using the Schedule class is deprecated, use '
            'The RunAtTimes or RunEveryMinutes classes instead',
            PendingDeprecationWarning
        )
        self.run_every_mins = run_every_mins
        self.run_at_times = run_at_times
        self.retry_after_failure_mins = retry_after_failure_mins

    def should_run_now(self, cron_job):
        if self.run_every_mins:
            return RunEveryMinutes(
                minutes=self.run_every_mins,
                retry_after_failure_mins=self.retry_after_failure_mins
            ).should_run_now(cron_job)
        if self.run_at_times:
            return RunAtTimes(
                times=self.run_at_times
            ).should_run_now(cron_job)
