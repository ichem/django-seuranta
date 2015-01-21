# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import seuranta.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Route',
            fields=[
                ('competitor', models.OneToOneField(related_name=b'defined_route', primary_key=True, serialize=False, to='seuranta.Competitor', verbose_name='route')),
                ('encoded_data', models.TextField(verbose_name='encoded data', blank=True)),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='last update date')),
                ('_start_datetime', models.DateTimeField(null=True, editable=False, blank=True)),
                ('_finish_datetime', models.DateTimeField(null=True, editable=False, blank=True)),
                ('_north', models.FloatField(blank=True, null=True, editable=False, validators=[seuranta.utils.validators.validate_latitude])),
                ('_south', models.FloatField(blank=True, null=True, editable=False, validators=[seuranta.utils.validators.validate_latitude])),
                ('_east', models.FloatField(blank=True, null=True, editable=False, validators=[seuranta.utils.validators.validate_longitude])),
                ('_west', models.FloatField(blank=True, null=True, editable=False, validators=[seuranta.utils.validators.validate_longitude])),
                ('_point_nb', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-update_date'],
                'verbose_name': 'route section',
                'verbose_name_plural': 'route sections',
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='routesection',
            name='competitor',
        ),
        migrations.DeleteModel(
            name='RouteSection',
        ),
        migrations.AlterField(
            model_name='map',
            name='calibration_string',
            field=models.CharField(help_text='Use online calibration tool if unsure', max_length=255, null=True, verbose_name='calibration string', blank=True),
        ),
    ]
