# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('default', '0003_alter_email_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSocialAuthCustom',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('default.usersocialauth',),
        ),
    ]
