# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0002_auto_20170403_1303'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competition',
            name='live_delay',
            field=models.PositiveIntegerField(help_text='delay of live in seconds', validators=[django.core.validators.MinValueValidator(10)], default=30, verbose_name='live delay'),
        ),
    ]
