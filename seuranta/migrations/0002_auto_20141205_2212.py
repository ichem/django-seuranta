# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='competition',
            old_name='map_display',
            new_name='display_mode',
        ),
        migrations.RenameField(
            model_name='competition',
            old_name='background_pattern',
            new_name='background_tile_url',
        ),
    ]
