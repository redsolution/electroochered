# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social_auth', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSocialAuthCustom',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('social_auth.usersocialauth',),
        ),
    ]
