import logging
from datetime import datetime, time, timedelta
import traceback
import warnings

from django_cron.models import CronJobLog
from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string
from django.db.models import Q


DEFAULT_LOCK_BACKEND = 'django_cron.backends.lock.cache.CacheLock'
logger = logging.getLogger('django_cron')


class Schedule(object):
    def __init__(self, run_every_mins=None, run_at_times=None, retry_after_failure_mins=None):
        if run_at_times is None:
            run_at_times = []
        self.run_every_mins = run_every_mins
        self.run_at_times = run_at_times
        self.retry_after_failure_mins = retry_after_failure_mins


class CronJobBase(object):
    """
    Sub-classes should have the following properties:
    + code - This should be a code specific to the cron being run. Eg. 'general.stats' etc.
    + schedule

    Following functions:
    + do - This is the actual business logic to be run at the given schedule
    """
    def __init__(self):
        self.prev_success_cron = None

    def get_prev_success_cron(self):
        warnings.warn(
            'CronJobBase.get_prev_success_cron() will soon be '
            'removed, use CronJobBase.prev_success_cron instead.',
            PendingDeprecationWarning
        )
        return self.prev_success_cron


class CronJobManager(object):
    """
    A manager instance should be created per cron job to be run.
    Does all the logger tracking etc. for it.
    Used as a context manager via 'with' statement to ensure
    proper logger in cases of job failure.
    """

    def __init__(self, cron_job_class):
        self.cron_job_class = cron_job_class
        self.lock_class = self.get_lock_class()
        self.last_successfully_ran_cron = None
        self.message = None

    def should_run_now(self, force=False):
        """
        Returns a boolean determining whether this cron should run now or not!
        Side-effect: will set self.last_successfully_ran_cron (for run_at_times only)
        """
        cron_job = self.cron_job

        # If we pass --force options, we force cron run
        if force:
            return True
        if cron_job.schedule.run_every_mins is not None:

            # We check last job - success or not
            last_job = None
            try:
                last_job = CronJobLog.objects.filter(code=cron_job.code).latest('start_time')
            except CronJobLog.DoesNotExist:
                pass
            if last_job \
               and not last_job.is_success \
               and cron_job.schedule.retry_after_failure_mins:
                next_retry_time = last_job.start_time + timedelta(minutes=cron_job.schedule.retry_after_failure_mins)
                return timezone.now() > next_retry_time

            try:
                self.last_successfully_ran_cron = CronJobLog.objects.filter(
                    code=cron_job.code,
                    is_success=True,
                    ran_at_time__isnull=True
                ).latest('start_time')
            except CronJobLog.DoesNotExist:
                pass

            if self.last_successfully_ran_cron:
                next_run_time = self.last_successfully_ran_cron.start_time \
                    + timedelta(minutes=cron_job.schedule.run_every_mins)
                return timezone.now() > next_run_time
            else:
                return True

        if cron_job.schedule.run_at_times:
            for scheduled_time in cron_job.schedule.run_at_times:
                scheduled_time = datetime.strptime(scheduled_time, "%H:%M").time()
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
                        self.cron_log.ran_at_time = scheduled_time
                        return True

        return False

    def clean_cron_log_message(self):
        if self.cron_log.message is None:
            self.cron_log.message = ''

        MESSAGE_MAX_LENGTH = 1000
        if len(self.cron_log.message) > MESSAGE_MAX_LENGTH:
            self.cron_log.message = self.cron_log.message[-MESSAGE_MAX_LENGTH:]

    def run(self, force=False, silent=False):
        """
        apply the logic of the schedule and call do() on the CronJobBase class
        """
        self.cron_log = CronJobLog(
            start_time=timezone.now(),
            code=self.cron_job_class.code
        )

        cron_job_class = self.cron_job_class

        try:
            with self.lock_class(cron_job_class, silent):
                self.cron_job = cron_job_class()

                if self.should_run_now(force):
                    logger.debug("Running cron: %s code %s", cron_job_class.__name__, self.cron_job.code)
                    self.cron_job.prev_success_cron = self.last_successfully_ran_cron

                    try:
                        self.cron_log.message = self.cron_job.do()
                        self.cron_log.is_success = True
                    except:
                        self.cron_log.message = traceback.format_exc()
                        self.cron_log.is_success = False

                    self.clean_cron_log_message()
                    self.cron_log.end_time = timezone.now()
                    self.cron_log.save()
        except self.lock_class.LockFailedException as e:
            if not silent:
                logger.info(e)

    def get_lock_class(self):
        name = getattr(settings, 'DJANGO_CRON_LOCK_BACKEND', DEFAULT_LOCK_BACKEND)
        try:
            return import_string(name)
        except ImportError as err:
            raise ImportError("invalid lock module %s. Can't use it: %s." % (name, err))
