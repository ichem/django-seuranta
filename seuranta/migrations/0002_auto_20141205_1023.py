# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='signup_policy',
            field=models.CharField(default=b'open', max_length=8, verbose_name='signup policy', choices=[(b'closed', 'Closed'), (b'org_val', 'Organizer Validated'), (b'open', 'Open')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competitor',
            name='approved',
            field=models.BooleanField(default=False, verbose_name='Approved by organizer'),
            preserve_default=True,
        ),
    ]
