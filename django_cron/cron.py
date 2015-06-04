from django.conf import settings
from django.utils.module_loading import import_string
from django_cron import CronJobBase, RunEveryMinutes
from django_cron.models import CronJobLog
from django_cron.settings import setting

from django_common.helper import send_mail


DEFAULT_MIN_NUM_FAILURES = 10


class FailedRunsNotificationCronJob(CronJobBase):
    """
    Send email if cron failed to run X times in a row
    """
    RUN_EVERY_MINS = 30

    schedule = RunEveryMinutes(minutes=RUN_EVERY_MINS)
    code = 'django_cron.FailedRunsNotificationCronJob'

    def do(self):

        CRONS_TO_CHECK = map(lambda x: import_string(x), settings.CRON_CLASSES)
        EMAILS = [admin[1] for admin in settings.ADMINS]
        FAILED_RUNS_CRONJOB_EMAIL_PREFIX = setting('EMAIL_PREFIX')

        for cron in CRONS_TO_CHECK:
            min_failures = getattr(cron, 'MIN_NUM_FAILURES',
                                   DEFAULT_MIN_NUM_FAILURES)
            failures = 0

            jobs = CronJobLog.objects.filter(code=cron.code).order_by('-end_time')[:min_failures]

            message = ''

            for job in jobs:
                if not job.is_success:
                    failures += 1
                    message += 'Job ran at %s : \n\n %s \n\n' % (job.start_time, job.message)

            if failures == min_failures:
                send_mail(
                    '%s%s failed %s times in a row!' % (
                        FAILED_RUNS_CRONJOB_EMAIL_PREFIX,
                        cron.code,
                        min_failures
                    ),
                    message,
                    settings.DEFAULT_FROM_EMAIL, EMAILS
                )
