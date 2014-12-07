# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import seuranta.models
import django.core.validators
from django.conf import settings
import timezone_field.fields
import seuranta.fields
import seuranta.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Competition',
            fields=[
                ('id', seuranta.fields.ShortUUIDField(primary_key=True, serialize=False, editable=False, verbose_name='identifier')),
                ('publish_date', models.DateTimeField(auto_now_add=True, verbose_name='publication date')),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='last update')),
                ('timezone', timezone_field.fields.TimeZoneField(default=b'UTC', verbose_name='timezone', tz_set_name=None, tz_choices=None)),
                ('start_date', models.DateTimeField(verbose_name='opening date (UTC)')),
                ('end_date', models.DateTimeField(verbose_name='closing date (UTC)')),
                ('name', models.CharField(default=b'Untitled', max_length=50, verbose_name='name', validators=[django.core.validators.MinLengthValidator(4)])),
                ('slug', models.SlugField(editable=False, max_length=21, validators=[seuranta.utils.validators.validate_nice_slug], unique=True, verbose_name='url friendly name')),
                ('publication_policy', models.CharField(default=b'public', max_length=8, verbose_name='publication policy', choices=[(b'private', 'Private'), (b'secret', 'Secret'), (b'public', 'Public')])),
                ('signup_policy', models.CharField(default=b'open', max_length=8, verbose_name='signup policy', choices=[(b'closed', 'Closed'), (b'org_val', 'Organizer Validated'), (b'open', 'Open')])),
                ('map', models.ImageField(upload_to=seuranta.models.map_upload_path, width_field=b'map_width', height_field=b'map_height', blank=True, null=True, verbose_name='map')),
                ('map_width', models.PositiveIntegerField(verbose_name='map width', null=True, editable=False, blank=True)),
                ('map_height', models.PositiveIntegerField(verbose_name='map height', null=True, editable=False, blank=True)),
                ('calibration_string', models.CharField(help_text="<a target='_blank' href='https://rphl.net/dropbox/calibrate_map2.html'>Online tool</a>", max_length=255, null=True, verbose_name='calibration string', blank=True)),
                ('map_display', models.CharField(default=b'map', max_length=8, verbose_name='display type', choices=[(b'map_bck', 'Map displayed over background'), (b'map', 'Map only'), (b'bck', 'Background')])),
                ('background_pattern', models.URLField(help_text='Leave blank to use OpenStreetMap as default', null=True, verbose_name='background pattern url', blank=True)),
                ('publisher', models.ForeignKey(related_name='competitions', editable=False, to=settings.AUTH_USER_MODEL, verbose_name='publisher')),
            ],
            options={
                'ordering': ['-start_date'],
                'verbose_name': 'competition',
                'verbose_name_plural': 'competitions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Competitor',
            fields=[
                ('id', seuranta.fields.ShortUUIDField(primary_key=True, serialize=False, editable=False, verbose_name='identifier')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('short_name', models.CharField(max_length=50, verbose_name='short name')),
                ('start_time', models.DateTimeField(null=True, verbose_name='start time (UTC)', blank=True)),
                ('api_token', seuranta.fields.ShortUUIDField(verbose_name='api token', null=True, editable=False)),
                ('access_code', models.CharField(default=b'', verbose_name='quick setup code', max_length=8, editable=False, blank=True)),
                ('approved', models.BooleanField(default=False, verbose_name='approved by organizer')),
                ('competition', models.ForeignKey(related_name='competitors', verbose_name='competition', to='seuranta.Competition')),
            ],
            options={
                'ordering': ['competition', 'start_time', 'name'],
                'verbose_name': 'competitor',
                'verbose_name_plural': 'competitors',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RouteSection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('encoded_data', models.TextField(verbose_name='encoded data', blank=True)),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='last update')),
                ('_start_datetime', models.DateTimeField(null=True, editable=False, blank=True)),
                ('_finish_datetime', models.DateTimeField(null=True, editable=False, blank=True)),
                ('_north', models.FloatField(blank=True, null=True, editable=False, validators=[seuranta.utils.validators.validate_latitude])),
                ('_south', models.FloatField(blank=True, null=True, editable=False, validators=[seuranta.utils.validators.validate_latitude])),
                ('_east', models.FloatField(blank=True, null=True, editable=False, validators=[seuranta.utils.validators.validate_longitude])),
                ('_west', models.FloatField(blank=True, null=True, editable=False, validators=[seuranta.utils.validators.validate_longitude])),
                ('competitor', models.ForeignKey(related_name='route_sections', verbose_name='competitor', to='seuranta.Competitor')),
            ],
            options={
                'ordering': ['-update_date'],
                'verbose_name': 'route section',
                'verbose_name_plural': 'route sections',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='competitor',
            unique_together=set([('api_token', 'competition'), ('access_code', 'competition')]),
        ),
    ]
