# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import seuranta.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0002_auto_20141205_2212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competition',
            name='background_tile_url',
            field=models.URLField(help_text='e.g https://{s}.example.com/{x}_{y}_{z}.png <br/>Leave blank to use OpenStreetMap', null=True, verbose_name='background tile url', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='calibration_string',
            field=models.CharField(help_text="<a target='_blank' href='https://rphl.net/dropbox/calibrate_map2.html'>Online calibration tool</a>", max_length=255, null=True, verbose_name='calibration string', blank=True),
            preserve_default=True,
        ),
    ]
