from django.db import models


class CronJobLog(models.Model):
    """
    Keeps track of the cron jobs that ran etc. and any error messages if they failed.
    """
    code = models.CharField(max_length=64, db_index=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    is_success = models.BooleanField(default=False)
    message = models.TextField(max_length=1000, blank=True)  # TODO: db_index=True

    # This field is provided so the schedule can store information
    # on cron job logs specific to their implementations.
    # For example, RunAtTimes needs to store the time the job ran.
    schedule_extra = models.TextField(blank=True, editable=False)

    def __unicode__(self):
        return '%s (%s)' % (self.code, 'Success' if self.is_success else 'Fail')

    class Meta:
        index_together = [
            ('code', 'is_success', 'schedule_extra'),
            ('code', 'start_time', 'schedule_extra'),
            ('code', 'start_time')  # useful when finding latest run (order by start_time) of cron
        ]
