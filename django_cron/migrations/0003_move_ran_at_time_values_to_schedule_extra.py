# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from django_cron.schedules import RunAtTimes


def move_ran_time_values(apps, schema_editor):
    CronJobLog = apps.get_model('django_cron', 'CronJobLog')

    for log in CronJobLog.objects.filter(ran_at_time__isnull=False):
        log.schedule_extra = RunAtTimes.format_time(log.ran_at_time)
        log.save()


class Migration(migrations.Migration):

    dependencies = [
        ('django_cron', '0002_cronjoblog_schedule_extra'),
    ]

    operations = [
        migrations.RunPython(move_ran_time_values),
    ]
