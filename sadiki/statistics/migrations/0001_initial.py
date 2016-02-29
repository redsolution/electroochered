# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StatisticsArchive',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('record_type', models.IntegerField(verbose_name='\u0422\u0438\u043f \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0438', choices=[(0, '\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430 \u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f \u043c\u0435\u0441\u0442'), (1, '\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430 \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u044f'), (2, '\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430 \u0432\u0440\u0435\u043c\u0435\u043d\u0438 \u043e\u0436\u0438\u0434\u0430\u043d\u0438\u044f \u0432 \u043e\u0447\u0435\u0440\u0435\u0434\u0438')])),
                ('data', models.TextField(verbose_name='\u0414\u0430\u043d\u043d\u044b\u0435 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0438')),
                ('date', models.DateField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430 \u043d\u0430 \u043a\u043e\u0442\u043e\u0440\u0443\u044e \u0430\u043a\u0442\u0443\u0430\u043b\u044c\u043d\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430')),
                ('year', models.DateField(verbose_name='\u0413\u043e\u0434 \u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f \u043a \u043a\u043e\u0442\u043e\u0440\u043e\u043c\u0443 \u043e\u0442\u043d\u043e\u0441\u0438\u0442\u0441\u044f \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430')),
            ],
        ),
    ]
