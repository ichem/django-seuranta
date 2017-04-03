# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import seuranta.utils.random_key


class Migration(migrations.Migration):

    dependencies = [
        ('seuranta', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competition',
            name='id',
            field=models.CharField(default=seuranta.utils.random_key.random_key, editable=False, max_length=12, serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='competitor',
            name='id',
            field=models.CharField(verbose_name='identifier', max_length=12, primary_key=True, default=seuranta.utils.random_key.random_key, editable=False, serialize=False),
        ),
        migrations.AlterField(
            model_name='route',
            name='id',
            field=models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True),
        ),
    ]
