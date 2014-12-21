# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import seuranta.models
import seuranta.storage


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0006_auto_20141207_1245'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='map',
            name='id',
        ),
        migrations.AlterField(
            model_name='map',
            name='competition',
            field=models.OneToOneField(related_name='defined_map', primary_key=True, serialize=False, to='seuranta.Competition'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='map',
            name='image',
            field=models.ImageField(upload_to=seuranta.models.map_upload_path, width_field=b'width', storage=seuranta.storage.OverwriteStorage(), height_field=b'height', blank=True, null=True, verbose_name='image'),
            preserve_default=True,
        ),
    ]
