# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0004_auto_20141205_2302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competitor',
            name='access_code',
            field=models.CharField(default=b'', verbose_name='access code', max_length=8, editable=False, blank=True),
            preserve_default=True,
        ),
    ]
