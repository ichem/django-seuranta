# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import seuranta.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0003_competition_live_delay'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competition',
            name='latitude',
            field=models.FloatField(default=0.0, verbose_name='latitude', validators=[seuranta.utils.validators.validate_latitude]),
        ),
        migrations.AlterField(
            model_name='competition',
            name='longitude',
            field=models.FloatField(default=0.0, verbose_name='longitude', validators=[seuranta.utils.validators.validate_longitude]),
        ),
        migrations.AlterField(
            model_name='competition',
            name='zoom',
            field=models.PositiveIntegerField(default=1, verbose_name='default zoom'),
        ),
    ]
