# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import seuranta.fields


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0002_auto_20141205_1023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competitor',
            name='tracker',
            field=seuranta.fields.ShortUUIDField(verbose_name='secret', null=True, editable=False),
            preserve_default=True,
        ),
    ]
