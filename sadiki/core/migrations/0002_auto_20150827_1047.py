# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='benefit',
            name='sadik_related',
            field=models.ManyToManyField(to='core.Sadik', verbose_name='\u0414\u041e\u0423 \u0432 \u043a\u043e\u0442\u043e\u0440\u044b\u0445 \u0435\u0441\u0442\u044c \u0433\u0440\u0443\u043f\u043f\u044b', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='sadiks',
            field=models.ManyToManyField(to='core.Sadik'),
        ),
    ]
