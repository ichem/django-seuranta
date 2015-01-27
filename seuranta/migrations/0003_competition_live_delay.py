# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0002_auto_20150121_0803'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='live_delay',
            field=models.PositiveIntegerField(default=30, help_text='delay of live in seconds', verbose_name='live delay'),
            preserve_default=True,
        ),
    ]
