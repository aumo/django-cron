# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_cron', '0003_move_ran_at_time_values_to_schedule_extra'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='cronjoblog',
            index_together=set([('code', 'start_time'), ('code', 'start_time', 'schedule_extra'), ('code', 'is_success', 'schedule_extra')]),
        ),
        migrations.RemoveField(
            model_name='cronjoblog',
            name='ran_at_time',
        ),
    ]
