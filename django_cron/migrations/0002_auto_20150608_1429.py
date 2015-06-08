# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_cron', '0001_initial'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='cronjoblog',
            index_together=set([('code', 'is_success'), ('code', 'start_time')]),
        ),
        migrations.RemoveField(
            model_name='cronjoblog',
            name='ran_at_time',
        ),
    ]
