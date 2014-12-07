# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0003_auto_20141205_2229'),
    ]

    operations = [
        migrations.AddField(
            model_name='routesection',
            name='_point_nb',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='display_mode',
            field=models.CharField(default=b'map', max_length=8, verbose_name='display mode', choices=[(b'map_bck', 'Map displayed over background'), (b'map', 'Map only'), (b'bck', 'Background')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='routesection',
            name='update_date',
            field=models.DateTimeField(auto_now=True, verbose_name='last update date'),
            preserve_default=True,
        ),
    ]
