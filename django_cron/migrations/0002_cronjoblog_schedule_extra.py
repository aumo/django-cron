# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_cron', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cronjoblog',
            name='schedule_extra',
            field=models.TextField(editable=False, blank=True),
        ),
    ]
