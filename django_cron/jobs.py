import logging
import traceback
import warnings

from django_cron.helpers import cached_property
from django_cron.models import CronJobLog

from django_cron.settings import setting
from django.utils import timezone
from django.utils.module_loading import import_string


logger = logging.getLogger('django_cron')


def get_lock_class():
    name = setting('LOCK_BACKEND')
    try:
        return import_string(name)
    except ImportError:
        raise ImportError("Invalid lock module, cannot import %s" % name)


class CronJobBase(object):
    """
    Base class for defining jobs run by django_cron.

    Sub-classes should have the following properties:
    + code - This should be a code specific to the cron being run.
      Eg. 'general.stats' etc.
    + schedule - a subclass of django_cron.schedules.BaseSchedule
      that defines when to run the job.

    Following methods:
    + do - This is the actual business logic to be run at the given schedule.
    """
    lock_class = get_lock_class()

    def __init__(self):
        self.cron_log = CronJobLog(
            start_time=timezone.now(),
            code=self.code
        )

    def get_prev_success_cron(self):
        warnings.warn(
            'CronJobBase.get_prev_success_cron() will soon be '
            'removed, use CronJobBase.last_successful_job instead.',
            PendingDeprecationWarning
        )
        return self.last_successful_job

    def clean_cron_log_message(self, message):
        '''
        Hook that allow subclasses to modify the cron
        log message.
        The default behaviour is to cut it at 1000 chars.
        '''
        MESSAGE_MAX_LENGTH = 1000
        if len(message) > MESSAGE_MAX_LENGTH:
            message = message[-MESSAGE_MAX_LENGTH:]
        return message

    @cached_property
    def last_job(self):
        '''
        Returns the CronJobLog of the last job sharing
        this CronJobBase's code.
        This property is cached so multiple calls won't
        run multiple database queries.
        '''
        try:
            return CronJobLog.objects \
                             .filter(code=self.code) \
                             .latest('start_time')
        except CronJobLog.DoesNotExist:
            pass

    @cached_property
    def last_successful_job(self):
        '''
        Returns the CronJobLog of the last successful job sharing
        this CronJobBase's code.
        This property is cached so multiple calls won't
        run multiple database queries.
        '''
        try:
            return CronJobLog.objects.filter(
                code=self.code,
                is_success=True,
                ran_at_time__isnull=True
            ).latest('start_time')
        except CronJobLog.DoesNotExist:
            pass

    def run(self, force=False, silent=False):
        """
        Apply the logic of the schedule and call do() on the CronJobBase class
        """
        try:
            with self.lock_class(self.__class__, silent):
                if force or self.schedule.should_run_now(self):
                    logger.debug("Running cron: %s code %s", self.__class__.__name__, self.code)

                    try:
                        message = self.do() or ''
                        self.cron_log.is_success = True
                    except:
                        message = traceback.format_exc()
                        self.cron_log.is_success = False

                    self.cron_log.message = self.clean_cron_log_message(message)
                    self.cron_log.end_time = timezone.now()
                    self.cron_log.save()
        except self.lock_class.LockFailedException as e:
            if not silent:
                logger.info(e)
