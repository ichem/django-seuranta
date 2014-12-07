# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import seuranta.models


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0005_auto_20141206_0006'),
    ]

    operations = [
        migrations.CreateModel(
            name='Map',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('image', models.ImageField(upload_to=seuranta.models.map_upload_path, width_field=b'width', height_field=b'height', blank=True, null=True, verbose_name='image')),
                ('width', models.PositiveIntegerField(verbose_name='width', null=True, editable=False, blank=True)),
                ('height', models.PositiveIntegerField(verbose_name='height', null=True, editable=False, blank=True)),
                ('calibration_string', models.CharField(help_text="<a target='_blank' href='https://rphl.net/dropbox/calibrate_map2.html'>Online calibration tool</a>", max_length=255, null=True, verbose_name='calibration string', blank=True)),
                ('display_mode', models.CharField(default=b'map', max_length=8, verbose_name='display mode', choices=[(b'map+bck', 'Map displayed over background'), (b'map', 'Map only'), (b'bck', 'Background')])),
                ('background_tile_url', models.URLField(help_text='e.g https://{s}.example.com/{x}_{y}_{z}.png <br/>Leave blank to use OpenStreetMap', null=True, verbose_name='background tile url', blank=True)),
                ('competition', models.OneToOneField(related_name='map', to='seuranta.Competition')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='competition',
            name='background_tile_url',
        ),
        migrations.RemoveField(
            model_name='competition',
            name='calibration_string',
        ),
        migrations.RemoveField(
            model_name='competition',
            name='display_mode',
        ),
        migrations.RemoveField(
            model_name='competition',
            name='map',
        ),
        migrations.RemoveField(
            model_name='competition',
            name='map_height',
        ),
        migrations.RemoveField(
            model_name='competition',
            name='map_width',
        ),
        migrations.AlterField(
            model_name='competitor',
            name='approved',
            field=models.BooleanField(default=False, verbose_name='approved'),
            preserve_default=True,
        ),
    ]
