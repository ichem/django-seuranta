# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0007_auto_20141208_1044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='map',
            name='background_tile_url',
            field=models.URLField(default='', help_text='e.g https://{s}.example.com/{x}_{y}_{z}.png, Leave blank to use OpenStreetMap', verbose_name='background tile url', blank=True),
            preserve_default=False,
        ),
    ]
