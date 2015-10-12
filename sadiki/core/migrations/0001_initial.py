# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sadiki.core.fields
import sadiki.core.validators
import django.contrib.gis.db.models.fields
import datetime
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chunks', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('town', models.CharField(max_length=255, null=True, verbose_name='\u041d\u0430\u0441\u0435\u043b\u0435\u043d\u043d\u044b\u0439 \u043f\u0443\u043d\u043a\u0442', blank=True)),
                ('street', models.CharField(max_length=255, null=True, verbose_name='\u0442\u0435\u043a\u0441\u0442 \u0430\u0434\u0440\u0435\u0441\u0430')),
                ('postindex', models.IntegerField(blank=True, null=True, verbose_name='\u043f\u043e\u0447\u0442\u043e\u0432\u044b\u0439 \u0438\u043d\u0434\u0435\u043a\u0441', validators=[django.core.validators.MaxValueValidator(999999)])),
                ('ocato', models.CharField(max_length=11, null=True, verbose_name='\u041e\u041a\u0410\u0422\u041e', blank=True)),
                ('block_number', models.CharField(max_length=255, null=True, verbose_name='\u2116 \u043a\u0432\u0430\u0440\u0442\u0430\u043b\u0430', blank=True)),
                ('building_number', models.CharField(max_length=255, null=True, verbose_name='\u2116 \u0437\u0434\u0430\u043d\u0438\u044f', blank=True)),
                ('extra_info', models.TextField(null=True, verbose_name='\u0434\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f', blank=True)),
                ('kladr', models.CharField(max_length=255, null=True, verbose_name='\u041a\u041b\u0410\u0414\u0420', blank=True)),
                ('coords', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, verbose_name='\u041a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442\u044b \u0442\u043e\u0447\u043a\u0438', blank=True)),
            ],
            options={
                'verbose_name': '\u0410\u0434\u0440\u0435\u0441',
                'verbose_name_plural': '\u0410\u0434\u0440\u0435\u0441\u0430',
            },
        ),
        migrations.CreateModel(
            name='AgeGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('short_name', models.CharField(max_length=100, null=True, verbose_name='\u043a\u043e\u0440\u043e\u0442\u043a\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('from_age', models.IntegerField(help_text='\u043f\u043e\u043b\u043d\u044b\u0445 \u043c\u0435\u0441\u044f\u0446\u0435\u0432 \u043d\u0430 \u0434\u0430\u0442\u0443 \u0438\u0441\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u044f \u043c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0430', verbose_name='\u041c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u044b\u0439 \u0432\u043e\u0437\u0440\u0430\u0441\u0442')),
                ('from_date', sadiki.core.fields.SplitDayMonthField(help_text='\u0443\u043a\u0430\u0436\u0438\u0442\u0435 \u0434\u0430\u0442\u0443(\u0447\u0438\u0441\u043b\u043e \u0438 \u043c\u0435\u0441\u044f\u0446) \u043d\u0430 \n        \u043a\u043e\u0442\u043e\u0440\u0443\u044e \u0431\u0443\u0434\u0435\u0442 \u0440\u0430\u0441\u0441\u0447\u0438\u0442\u044b\u0432\u0430\u0442\u044c\u0441\u044f \u043c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u044b\u0439 \u0432\u043e\u0437\u0440\u0430\u0441\u0442', max_length=10, verbose_name='\u0414\u0430\u0442\u0430 \u0438\u0441\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u044f \u043c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0430')),
                ('to_age', models.IntegerField(help_text='\u043f\u043e\u043b\u043d\u044b\u0445 \u043c\u0435\u0441\u044f\u0446\u0435\u0432 \u043d\u0430 \u0434\u0430\u0442\u0443 \u0438\u0441\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u044f \u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0430', verbose_name='\u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u044b\u0439 \u0432\u043e\u0437\u0440\u0430\u0441\u0442')),
                ('to_date', sadiki.core.fields.SplitDayMonthField(help_text='\u0443\u043a\u0430\u0436\u0438\u0442\u0435 \u0434\u0430\u0442\u0443(\u0447\u0438\u0441\u043b\u043e \u0438 \u043c\u0435\u0441\u044f\u0446) \u043d\u0430 \n        \u043a\u043e\u0442\u043e\u0440\u0443\u044e \u0431\u0443\u0434\u0435\u0442 \u0440\u0430\u0441\u0441\u0447\u0438\u0442\u044b\u0432\u0430\u0442\u044c\u0441\u044f \u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u044b\u0439 \u0432\u043e\u0437\u0440\u0430\u0441\u0442', max_length=10, verbose_name='\u0414\u0430\u0442\u0430 \u0438\u0441\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u044f \u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0430')),
                ('next_age_group', models.ForeignKey(verbose_name='\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0430\u044f \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u043d\u0430\u044f \u0433\u0440\u0443\u043f\u043f\u0430', blank=True, to='core.AgeGroup', null=True)),
            ],
            options={
                'ordering': ['from_age'],
                'verbose_name': '\u0412\u043e\u0437\u0440\u0430\u0441\u0442\u043d\u0430\u044f \u0433\u0440\u0443\u043f\u043f\u0430 \u0434\u043b\u044f \u0441\u0438\u0441\u0442\u0435\u043c\u044b',
                'verbose_name_plural': '\u0412\u043e\u0437\u0440\u0430\u0441\u0442\u043d\u044b\u0435 \u0433\u0440\u0443\u043f\u043f\u044b \u0434\u043b\u044f \u0441\u0438\u0441\u0442\u0435\u043c\u044b',
            },
        ),
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('ocato', models.CharField(max_length=11, verbose_name='\u041e\u041a\u0410\u0422\u041e')),
                ('bounds', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, verbose_name='\u0413\u0440\u0430\u043d\u0438\u0446\u044b \u043e\u0431\u043b\u0430\u0441\u0442\u0438', blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': '\u0433\u0440\u0443\u043f\u043f\u0430 \u0441\u0430\u0434\u0438\u043a\u043e\u0432',
                'verbose_name_plural': '\u0433\u0440\u0443\u043f\u043f\u044b \u0441\u0430\u0434\u0438\u043a\u043e\u0432',
            },
        ),
        migrations.CreateModel(
            name='Benefit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(blank=True, null=True, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(1, '\u0420\u0435\u0433\u0438\u043e\u043d\u0430\u043b\u044c\u043d\u0430\u044f'), (2, '\u0424\u0435\u0434\u0435\u0440\u0430\u043b\u044c\u043d\u0430\u044f')])),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='\u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('description', models.CharField(max_length=255, verbose_name='\u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('disabled', models.BooleanField(default=False, help_text='\u041e\u0442\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 \u043d\u0435 \u0443\u0434\u0430\u043b\u044f\u0435\u0442 \u043b\u044c\u0433\u043e\u0442\u0443 \u0443 \u0437\u0430\u044f\u0432\u043e\u043a, \u0430 \u0442\u043e\u043b\u044c\u043a\u043e \u043d\u0435 \u0434\u0430\u0435\u0442 \u0432\u044b\u0431\u0440\u0430\u0442\u044c \u0435\u0451 \u043f\u0440\u0438 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438.', verbose_name='\u041e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u044c')),
            ],
            options={
                'verbose_name': '\u041b\u044c\u0433\u043e\u0442\u0430',
                'verbose_name_plural': '\u041b\u044c\u0433\u043e\u0442\u044b',
            },
        ),
        migrations.CreateModel(
            name='BenefitCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('description', models.CharField(max_length=255, null=True, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435')),
                ('priority', models.PositiveIntegerField(help_text='\u0427\u0435\u043c \u0431\u043e\u043b\u044c\u0448\u0435 \u0447\u0438\u0441\u043b\u043e, \u0442\u0435\u043c \u0432\u044b\u0448\u0435 \u043f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442', unique=True, verbose_name='\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442\u043d\u043e\u0441\u0442\u044c \u043b\u044c\u0433\u043e\u0442\u044b', validators=[django.core.validators.MaxValueValidator(99)])),
                ('immediately_distribution_active', models.BooleanField(default=False, verbose_name='\u0423\u0447\u0430\u0432\u0441\u0442\u0432\u0443\u0435\u0442 \u0432 \u043d\u0435\u043c\u0435\u0434\u043b\u0435\u043d\u043d\u043e\u043c \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u0438')),
            ],
            options={
                'verbose_name': '\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u043b\u044c\u0433\u043e\u0442',
                'verbose_name_plural': '\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438 \u043b\u044c\u0433\u043e\u0442',
            },
        ),
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('init_datetime', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f \u043d\u0430\u0447\u0430\u043b\u0430 \u0432\u044b\u0434\u0435\u043b\u0435\u043d\u0438\u044f \u043c\u0435\u0441\u0442')),
                ('start_datetime', models.DateTimeField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f \u043d\u0430\u0447\u0430\u043b\u0430 \u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f', blank=True)),
                ('end_datetime', models.DateTimeField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f \u043e\u043a\u043e\u043d\u0447\u0430\u043d\u0438\u044f', blank=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u0422\u0435\u043a\u0443\u0449\u0438\u0439 \u0441\u0442\u0430\u0442\u0443\u0441', choices=[(0, '\u0420\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435 \u043d\u0430\u0447\u0430\u0442\u043e'), (3, '\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\u043e\u0432\u0430\u043d\u0438\u0435'), (1, '\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\u0430\u0446\u0438\u044f \u0437\u0430\u044f\u0432\u043e\u043a'), (4, '\u041f\u0440\u043e\u0446\u0435\u0441\u0441 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0438\u044f \u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f'), (2, '\u0420\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e')])),
                ('year', models.DateField(verbose_name='\u0413\u043e\u0434 \u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f')),
            ],
            options={
                'ordering': ['end_datetime'],
                'verbose_name': '\u0420\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435',
                'verbose_name_plural': '\u0420\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f',
            },
        ),
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0440\u0430\u0439\u043e\u043d\u0430')),
            ],
            options={
                'verbose_name': '\u0420\u0430\u0439\u043e\u043d',
                'verbose_name_plural': '\u0420\u0430\u0439\u043e\u043d\u044b',
            },
        ),
        migrations.CreateModel(
            name='EvidienceDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document_number', models.CharField(max_length=255, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430')),
                ('confirmed', models.NullBooleanField(default=None, verbose_name='\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d')),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('fake', models.BooleanField(default=False, verbose_name='\u0411\u044b\u043b \u0441\u0433\u0435\u043d\u0435\u0440\u0438\u0440\u043e\u0432\u0430\u043d \u043f\u0440\u0438 \u0438\u043c\u043f\u043e\u0440\u0442\u0435')),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'verbose_name': '\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442',
                'verbose_name_plural': '\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b',
            },
        ),
        migrations.CreateModel(
            name='EvidienceDocumentTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('format_tips', models.CharField(max_length=255, verbose_name='\u043f\u043e\u0434\u0441\u043a\u0430\u0437\u043a\u0430 \u043a \u0444\u043e\u0440\u043c\u0430\u0442\u0443', blank=True)),
                ('destination', models.IntegerField(verbose_name='\u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430', choices=[(0, '\u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u0446\u0438\u0440\u0443\u0435\u0442 \u0440\u043e\u0434\u0438\u0442\u0435\u043b\u044f'), (1, '\u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u0446\u0438\u0440\u0443\u0435\u0442 \u0440\u0435\u0431\u0451\u043d\u043a\u0430'), (2, '\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b \u043a \u043b\u044c\u0433\u043e\u0442\u0430\u043c')])),
                ('regex', models.TextField(verbose_name='\u0420\u0435\u0433\u0443\u043b\u044f\u0440\u043d\u043e\u0435 \u0432\u044b\u0440\u0430\u0436\u0435\u043d\u0438\u0435')),
                ('import_involved', models.BooleanField(default=False, verbose_name='\u0423\u0447\u0438\u0442\u044b\u0432\u0430\u0435\u0442\u0441\u044f \u043f\u0440\u0438 \u0438\u043c\u043f\u043e\u0440\u0442\u0435')),
                ('gives_health_impairment', models.BooleanField(verbose_name='\u041e\u0442\u043c\u0435\u0447\u0430\u0435\u0442 \u0440\u0435\u0431\u0435\u043d\u043a\u0430 \u0441 \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u043d\u044b\u043c\u0438 \u0432\u043e\u0437\u043c\u043e\u0436\u043d\u043e\u0441\u0442\u044f\u043c\u0438 \u0437\u0434\u043e\u0440\u043e\u0432\u044c\u044f')),
                ('gives_compensating_group', models.BooleanField(verbose_name='\u041f\u0440\u0435\u0434\u043e\u0441\u0442\u0430\u0432\u043b\u044f\u0435\u0442 \u0432\u043e\u0437\u043c\u043e\u0436\u043d\u043e\u0441\u0442\u044c \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u044f \u0432 \u0433\u0440\u0443\u043f\u043f\u0443 \u043a\u043e\u043c\u043f\u0435\u043d\u0441\u0438\u0440\u0443\u044e\u0449\u0435\u0439 \u043d\u0430\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043d\u043e\u0441\u0442\u0438')),
                ('gives_wellness_group', models.BooleanField(verbose_name='\u041f\u0440\u0435\u0434\u043e\u0441\u0442\u0430\u0432\u043b\u044f\u0435\u0442 \u0432\u043e\u0437\u043c\u043e\u0436\u043d\u043e\u0441\u0442\u044c \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u044f \u0432 \u0433\u0440\u0443\u043f\u043f\u0443 \u043e\u0437\u0434\u043e\u0440\u043e\u0432\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0439 \u043d\u0430\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043d\u043e\u0441\u0442\u0438')),
            ],
            options={
                'verbose_name': '\u0422\u0438\u043f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430',
                'verbose_name_plural': '\u0422\u0438\u043f\u044b \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432',
            },
        ),
        migrations.CreateModel(
            name='PersonalDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('doc_type', models.IntegerField(default=2, verbose_name='\u0422\u0438\u043f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430', choices=[(2, '\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u0433\u0440\u0430\u0436\u0434\u0430\u043d\u0438\u043d\u0430 \u0420\u0424'), (1, '\u0418\u043d\u043e\u0435')])),
                ('doc_name', models.CharField(max_length=30, null=True, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430', blank=True)),
                ('series', models.CharField(max_length=20, null=True, verbose_name='\u0421\u0435\u0440\u0438\u044f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430', blank=True)),
                ('number', models.CharField(max_length=50, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430')),
                ('issued_date', models.DateField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0432\u044b\u0434\u0430\u0447\u0438 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430')),
                ('issued_by', models.CharField(max_length=250, null=True, verbose_name='\u041a\u0435\u043c \u0432\u044b\u0434\u0430\u043d', blank=True)),
            ],
            options={
                'verbose_name': '\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442 \u0437\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u044f',
                'verbose_name_plural': '\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b \u0437\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u0435\u0439',
            },
        ),
        migrations.CreateModel(
            name='Preference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('section', models.CharField(max_length=255, verbose_name='\u0420\u0430\u0437\u0434\u0435\u043b', choices=[(b'municipality', '\u0420\u0430\u0437\u0434\u0435\u043b \u0441 \u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u0430\u043c\u0438 \u043c\u0443\u043d\u0438\u0446\u0438\u043f\u0430\u043b\u0438\u0442\u0435\u0442\u0430'), (b'system', '\u0421\u0438\u0441\u0442\u0435\u043c\u043d\u044b\u0435 \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438'), (b'hidden', '\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438, \u043a\u043e\u0442\u043e\u0440\u044b\u0435 \u043c\u043e\u0433\u0443\u0442 \u0438\u0437\u043c\u0435\u043d\u044f\u0442\u044c\u0441\u044f \u0442\u043e\u043b\u044c\u043a\u043e \u0441\u0438\u0441\u0442\u0435\u043c\u043e\u0439')])),
                ('key', models.CharField(unique=True, max_length=255, verbose_name='\u041a\u043b\u044e\u0447', choices=[(b'MUNICIPALITY_NAME', '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043c\u0443\u043d\u0438\u0446\u0438\u043f\u0430\u043b\u0438\u0442\u0435\u0442\u0430'), (b'MUNICIPALITY_NAME_GENITIVE', '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043c\u0443\u043d\u0438\u0446\u0438\u043f\u0430\u043b\u0438\u0442\u0435\u0442\u0430 (\u0440\u043e\u0434\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u043f\u0430\u0434\u0435\u0436)'), (b'MUNICIPALITY_PHONE', '\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u043d\u044b\u0439 \u0442\u0435\u043b\u0435\u0444\u043e\u043d'), (b'EMAIL_KEY_VALID', '\u0421\u0440\u043e\u043a \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f \u043a\u043b\u044e\u0447\u0430 \u0434\u043b\u044f \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f \u043f\u043e\u0447\u0442\u044b(\u0434\u043d\u0435\u0439)'), (b'IMPORT_STATUS_FINISHED', '\u0421\u0442\u0430\u0442\u0443\u0441 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0438\u044f \u0438\u043c\u043f\u043e\u0440\u0442\u0430'), (b'REQUESTIONS_IMPORTED', '\u0411\u044b\u043b\u0438 \u0438\u043c\u043f\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u044b \u0437\u0430\u044f\u0432\u043a\u0438'), (b'LOCAL_AUTHORITY', '\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043e\u0440\u0433\u0430\u043d\u0430 \u043c\u0435\u0441\u0442\u043d\u043e\u0433\u043e \u0441\u0430\u043c\u043e\u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f, \n        \u043e\u0441\u0443\u0449\u0435\u0441\u0442\u0432\u043b\u044f\u044e\u0449\u0435\u0433\u043e \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0432 \u0441\u0444\u0435\u0440\u0435 \u043e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u043d\u0438\u044f (\u0440\u043e\u0434\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u043f\u0430\u0434\u0435\u0436)'), (b'AUTHORITY_HEAD', '\u0424\u0418\u041e \u0433\u043b\u0430\u0432\u044b \u043e\u0440\u0433\u0430\u043d\u0430 \u043c\u0435\u0441\u0442\u043d\u043e\u0433\u043e \u0441\u0430\u043c\u043e\u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f,\n        \u043e\u0441\u0443\u0449\u0435\u0441\u0442\u0432\u043b\u044f\u044e\u0449\u0435\u0433\u043e \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0432 \u0441\u0444\u0435\u0440\u0435 \u043e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u043d\u0438\u044f (\u0434\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u043f\u0430\u0434\u0435\u0436)')])),
                ('datetime', models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0433\u043e \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f')),
                ('value', models.CharField(max_length=255, verbose_name='\u0417\u043d\u0430\u0447\u0435\u043d\u0438\u0435')),
            ],
            options={
                'verbose_name': '\u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0440',
                'verbose_name_plural': '\u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('middle_name', models.CharField(max_length=255, null=True, verbose_name='\u041e\u0442\u0447\u0435\u0441\u0442\u0432\u043e', blank=True)),
                ('email_verified', models.BooleanField(default=False, verbose_name='E-mail \u0434\u043e\u0441\u0442\u043e\u0432\u0435\u0440\u043d\u044b\u0439')),
                ('phone_number', models.CharField(max_length=255, null=True, verbose_name='\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043b\u044f \u0441\u0432\u044f\u0437\u0438', blank=True)),
                ('mobile_number', models.CharField(max_length=255, null=True, verbose_name='\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u043b\u0435\u0444\u043e\u043d', blank=True)),
                ('skype', models.CharField(help_text='\u0423\u0447\u0435\u0442\u043d\u0430\u044f \u0437\u0430\u043f\u0438\u0441\u044c \u0432 \u0441\u0435\u0440\u0432\u0438\u0441\u0435 Skype', max_length=255, null=True, verbose_name='Skype', blank=True)),
                ('snils', models.CharField(validators=[django.core.validators.RegexValidator(b'^[0-9]{3}-[0-9]{3}-[0-9]{3} [0-9]{2}$', message='\u043d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442')], max_length=20, blank=True, help_text='\u0424\u043e\u0440\u043c\u0430\u0442: 123-456-789 12', null=True, verbose_name='\u0421\u041d\u0418\u041b\u0421')),
                ('town', models.CharField(max_length=50, null=True, verbose_name='\u041d\u0430\u0441\u0435\u043b\u0451\u043d\u043d\u044b\u0439 \u043f\u0443\u043d\u043a\u0442')),
                ('street', models.CharField(max_length=50, null=True, verbose_name='\u0423\u043b\u0438\u0446\u0430')),
                ('house', models.CharField(max_length=10, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0434\u043e\u043c\u0430')),
                ('social_auth_public', models.NullBooleanField(verbose_name='\u041f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0442\u044c \u043c\u043e\u0439 \u043f\u0440\u043e\u0444\u0438\u043b\u044c \u0412\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u0435 \u0432 \u043f\u0443\u0431\u043b\u0438\u0447\u043d\u043e\u0439 \u043e\u0447\u0435\u0440\u0435\u0434\u0438', choices=[(True, b'\xd0\x9e\xd1\x82\xd0\xbe\xd0\xb1\xd1\x80\xd0\xb0\xd0\xb6\xd0\xb0\xd1\x82\xd1\x8c \xd0\xb2 \xd0\xbf\xd1\x83\xd0\xb1\xd0\xbb\xd0\xb8\xd1\x87\xd0\xbd\xd0\xbe\xd0\xb9 \xd0\xbe\xd1\x87\xd0\xb5\xd1\x80\xd0\xb5\xd0\xb4\xd0\xb8'), (False, b'\xd0\x9d\xd0\xb5 \xd0\xbe\xd1\x82\xd0\xbe\xd0\xb1\xd1\x80\xd0\xb0\xd0\xb6\xd0\xb0\xd1\x82\xd1\x8c \xd0\xb2 \xd0\xbf\xd1\x83\xd0\xb1\xd0\xbb\xd0\xb8\xd1\x87\xd0\xbd\xd0\xbe\xd0\xb9 \xd0\xbe\xd1\x87\xd0\xb5\xd1\x80\xd0\xb5\xd0\xb4\xd0\xb8')])),
                ('pd_processing_permit', models.DateTimeField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0441\u043e\u0433\u043b\u0430\u0441\u0438\u044f \u043d\u0430 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0443 \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u044c\u043d\u044b\u0445 \u0434\u0430\u043d\u043d\u044b\u0445', blank=True)),
                ('area', models.ForeignKey(verbose_name='\u0422\u0435\u0440\u0440\u0438\u0442\u043e\u0440\u0438\u0430\u043b\u044c\u043d\u0430\u044f \u043e\u0431\u043b\u0430\u0441\u0442\u044c \u043a \u043a\u043e\u0442\u043e\u0440\u043e\u0439 \u043e\u0442\u043d\u043e\u0441\u0438\u0442\u0441\u044f', to='core.Area', null=True)),
            ],
            options={
                'verbose_name': '\u041f\u0440\u043e\u0444\u0438\u043b\u044c \u0440\u043e\u0434\u0438\u0442\u0435\u043b\u044f',
                'verbose_name_plural': '\u041f\u0440\u043e\u0444\u0438\u043b\u0438 \u0440\u043e\u0434\u0438\u0442\u0435\u043b\u0435\u0439',
            },
        ),
        migrations.CreateModel(
            name='Requestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('admission_date', models.DateField(help_text='\u0414\u0430\u0442\u0430, \u043d\u0430\u0447\u0438\u043d\u0430\u044f \u0441 \u043a\u043e\u0442\u043e\u0440\u043e\u0439 \u0437\u0430\u044f\u0432\u043a\u0430 \u043c\u043e\u0436\u0435\u0442 \u0431\u044b\u0442\u044c \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0430', null=True, verbose_name='\u0416\u0435\u043b\u0430\u0435\u043c\u0430\u044f \u0434\u0430\u0442\u0430 \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u044f', blank=True)),
                ('requestion_number', models.CharField(max_length=23, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0437\u0430\u044f\u0432\u043a\u0438', blank=True)),
                ('distribution_type', models.IntegerField(default=0, verbose_name='\u0442\u0438\u043f \u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f', choices=[(0, '\u041e\u0431\u044b\u0447\u043d\u043e\u0435 \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u0435'), (1, '\u0417\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u0435 \u043d\u0430 \u043f\u043e\u0441\u0442\u043e\u044f\u043d\u043d\u043e\u0439 \u043e\u0441\u043d\u043e\u0432\u0435')])),
                ('birth_date', models.DateField(verbose_name='\u0414\u0430\u0442\u0430 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u0440\u0435\u0431\u0451\u043d\u043a\u0430', validators=[sadiki.core.validators.birth_date_validator])),
                ('name', models.CharField(max_length=255, null=True, verbose_name='\u0418\u043c\u044f \u0440\u0435\u0431\u0451\u043d\u043a\u0430', validators=[sadiki.core.fields.validate_no_spaces])),
                ('child_middle_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='\u041e\u0442\u0447\u0435\u0441\u0442\u0432\u043e \u0440\u0435\u0431\u0451\u043d\u043a\u0430', validators=[sadiki.core.fields.validate_no_spaces])),
                ('child_last_name', models.CharField(max_length=50, null=True, verbose_name='\u0424\u0430\u043c\u0438\u043b\u0438\u044f \u0440\u0435\u0431\u0451\u043d\u043a\u0430', validators=[sadiki.core.fields.validate_no_spaces])),
                ('sex', models.CharField(max_length=1, null=True, verbose_name='\u041f\u043e\u043b \u0440\u0435\u0431\u0451\u043d\u043a\u0430', choices=[('\u041c', '\u041c\u0443\u0436\u0441\u043a\u043e\u0439'), ('\u0416', '\u0416\u0435\u043d\u0441\u043a\u0438\u0439')])),
                ('kinship', models.CharField(max_length=50, null=True, verbose_name='\u0421\u0442\u0435\u043f\u0435\u043d\u044c \u0440\u043e\u0434\u0441\u0442\u0432\u0430 \u0437\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u044f', blank=True)),
                ('birthplace', models.CharField(max_length=50, null=True, verbose_name='\u041c\u0435\u0441\u0442\u043e \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u0440\u0435\u0431\u0451\u043d\u043a\u0430')),
                ('child_snils', models.CharField(validators=[django.core.validators.RegexValidator(b'^[0-9]{3}-[0-9]{3}-[0-9]{3} [0-9]{2}$', message='\u043d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442')], max_length=20, blank=True, help_text='\u0424\u043e\u0440\u043c\u0430\u0442: 123-456-789 12', null=True, verbose_name='\u0421\u041d\u0418\u041b\u0421 \u0440\u0435\u0431\u0451\u043d\u043a\u0430')),
                ('cast', models.IntegerField(default=3, verbose_name='\u0422\u0438\u043f \u0437\u0430\u044f\u0432\u043a\u0438', choices=[(0, '\u0420\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f \u0447\u0435\u0440\u0435\u0437 \u043e\u043f\u0435\u0440\u0430\u0442\u043e\u0440\u0430'), (1, '\u0418\u043c\u043f\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u0430\u044f \u0437\u0430\u044f\u0432\u043a\u0430'), (2, '\u0417\u0430\u044f\u0432\u043a\u0430 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u0430 \u0434\u043e \u0437\u0430\u043f\u0443\u0441\u043a\u0430 \u0441\u0438\u0441\u0442\u0435\u043c\u044b \u0438 \u0432\u0432\u0435\u0434\u0435\u043d\u0430 \u0432\u0440\u0443\u0447\u043d\u0443\u044e'), (3, 'C\u0430\u043c\u043e\u0441\u0442\u043e\u044f\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f')])),
                ('status', models.IntegerField(default=3, null=True, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(1, '\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u0440\u0430\u0441\u0441\u043c\u043e\u0442\u0440\u0435\u043d\u0438\u044f'), (2, '\u0417\u0430\u044f\u0432\u043b\u0435\u043d\u0438\u0435 \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043e'), (3, '\u041e\u0447\u0435\u0440\u0435\u0434\u043d\u0438\u043a - \u043d\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d'), (4, '\u041e\u0447\u0435\u0440\u0435\u0434\u043d\u0438\u043a'), (6, '\u0412\u044b\u0434\u0435\u043b\u0435\u043d\u043e \u043c\u0435\u0441\u0442\u043e'), (9, '\u0412\u044b\u0434\u0430\u043d\u0430 \u043f\u0443\u0442\u0435\u0432\u043a\u0430'), (12, '\u0412\u044b\u0434\u0430\u043d\u0430 \u043f\u0443\u0442\u0435\u0432\u043a\u0430 \u043d\u0430 \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u0439 \u043e\u0441\u043d\u043e\u0432\u0435'), (13, '\u0417\u0430\u0447\u0438\u0441\u043b\u0435\u043d'), (14, '\u0412\u0440\u0435\u043c\u0435\u043d\u043d\u043e \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d'), (15, '\u041e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u0435\u0442'), (16, '\u041d\u0435 \u044f\u0432\u0438\u043b\u0441\u044f'), (17, '\u0421\u043d\u044f\u0442 \u0441 \u0443\u0447\u0451\u0442\u0430'), (18, '\u0410\u0440\u0445\u0438\u0432\u043d\u0430\u044f'), (50, '\u041d\u0430 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\u043e\u0432\u0430\u043d\u0438\u0438'), (51, '\u041d\u0430 \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u043c \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\u043e\u0432\u0430\u043d\u0438\u0438'), (53, '\u0421\u0440\u043e\u043a\u0438 \u043d\u0430 \u043e\u0431\u0436\u0430\u043b\u043e\u0432\u0430\u043d\u0438\u0435 \u043d\u0435\u044f\u0432\u043a\u0438 \u0438\u0441\u0442\u0435\u043a\u043b\u0438'), (54, '\u0421\u0440\u043e\u043a\u0438 \u043d\u0430 \u043e\u0431\u0436\u0430\u043b\u043e\u0432\u0430\u043d\u0438\u0435 \u043e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u044f \u0438\u0441\u0442\u0435\u043a\u043b\u0438'), (55, '\u0414\u043b\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u043e\u0442\u0441\u0443\u0442\u0441\u0432\u0438\u0435 \u043f\u043e \u0443\u0432\u0430\u0436\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0439 \u043f\u0440\u0438\u0447\u0438\u043d\u0435'), (56, '\u0417\u0430\u0447\u0438\u0441\u043b\u0435\u043d'), (57, '\u041f\u043e\u0441\u0435\u0449\u0430\u0435\u0442 \u0433\u0440\u0443\u043f\u043f\u0443 \u043a\u0440\u0430\u0442\u043a\u043e\u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u0433\u043e \u043f\u0440\u0435\u0431\u044b\u0432\u0430\u043d\u0438\u044f'), (58, '\u0412\u044b\u043f\u0443\u0449\u0435\u043d \u0438\u0437 \u0414\u041e\u0423')])),
                ('previous_status', models.IntegerField(blank=True, null=True, verbose_name='\u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439 \u0441\u0442\u0430\u0442\u0443\u0441', choices=[(1, '\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u0440\u0430\u0441\u0441\u043c\u043e\u0442\u0440\u0435\u043d\u0438\u044f'), (2, '\u0417\u0430\u044f\u0432\u043b\u0435\u043d\u0438\u0435 \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043e'), (3, '\u041e\u0447\u0435\u0440\u0435\u0434\u043d\u0438\u043a - \u043d\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d'), (4, '\u041e\u0447\u0435\u0440\u0435\u0434\u043d\u0438\u043a'), (6, '\u0412\u044b\u0434\u0435\u043b\u0435\u043d\u043e \u043c\u0435\u0441\u0442\u043e'), (9, '\u0412\u044b\u0434\u0430\u043d\u0430 \u043f\u0443\u0442\u0435\u0432\u043a\u0430'), (12, '\u0412\u044b\u0434\u0430\u043d\u0430 \u043f\u0443\u0442\u0435\u0432\u043a\u0430 \u043d\u0430 \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u0439 \u043e\u0441\u043d\u043e\u0432\u0435'), (13, '\u0417\u0430\u0447\u0438\u0441\u043b\u0435\u043d'), (14, '\u0412\u0440\u0435\u043c\u0435\u043d\u043d\u043e \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d'), (15, '\u041e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u0435\u0442'), (16, '\u041d\u0435 \u044f\u0432\u0438\u043b\u0441\u044f'), (17, '\u0421\u043d\u044f\u0442 \u0441 \u0443\u0447\u0451\u0442\u0430'), (18, '\u0410\u0440\u0445\u0438\u0432\u043d\u0430\u044f'), (50, '\u041d\u0430 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\u043e\u0432\u0430\u043d\u0438\u0438'), (51, '\u041d\u0430 \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u043c \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\u043e\u0432\u0430\u043d\u0438\u0438'), (53, '\u0421\u0440\u043e\u043a\u0438 \u043d\u0430 \u043e\u0431\u0436\u0430\u043b\u043e\u0432\u0430\u043d\u0438\u0435 \u043d\u0435\u044f\u0432\u043a\u0438 \u0438\u0441\u0442\u0435\u043a\u043b\u0438'), (54, '\u0421\u0440\u043e\u043a\u0438 \u043d\u0430 \u043e\u0431\u0436\u0430\u043b\u043e\u0432\u0430\u043d\u0438\u0435 \u043e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u044f \u0438\u0441\u0442\u0435\u043a\u043b\u0438'), (55, '\u0414\u043b\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u043e\u0442\u0441\u0443\u0442\u0441\u0432\u0438\u0435 \u043f\u043e \u0443\u0432\u0430\u0436\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0439 \u043f\u0440\u0438\u0447\u0438\u043d\u0435'), (56, '\u0417\u0430\u0447\u0438\u0441\u043b\u0435\u043d'), (57, '\u041f\u043e\u0441\u0435\u0449\u0430\u0435\u0442 \u0433\u0440\u0443\u043f\u043f\u0443 \u043a\u0440\u0430\u0442\u043a\u043e\u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u0433\u043e \u043f\u0440\u0435\u0431\u044b\u0432\u0430\u043d\u0438\u044f'), (58, '\u0412\u044b\u043f\u0443\u0449\u0435\u043d \u0438\u0437 \u0414\u041e\u0423')])),
                ('registration_datetime', models.DateTimeField(default=datetime.datetime.now, verbose_name='\u0414\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f \u043f\u043e\u0434\u0430\u0447\u0438 \u0437\u0430\u044f\u0432\u043a\u0438', validators=[sadiki.core.validators.registration_date_validator])),
                ('number_in_old_list', models.CharField(max_length=15, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0432 \u0431\u0443\u043c\u0430\u0436\u043d\u043e\u043c \u0441\u043f\u0438\u0441\u043a\u0435', blank=True)),
                ('location', django.contrib.gis.db.models.fields.PointField(help_text='\u041e\u0442\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c\u043d\u043e \u044d\u0442\u043e\u0433\u043e \u043c\u0435\u0441\u0442\u043e\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u0431\u0443\u0434\u0443\u0442 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u044f\u0442\u0441\u044f \u0431\u043b\u0438\u0436\u0430\u0439\u0448\u0438\u0435 \u0414\u041e\u0423', srid=4326, null=True, verbose_name='\u041c\u0435\u0441\u0442\u043e\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u0435', blank=True)),
                ('location_properties', models.CharField(max_length=250, null=True, verbose_name='\u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b \u043c\u0435\u0441\u0442\u043e\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f', blank=True)),
                ('status_change_datetime', models.DateTimeField(null=True, verbose_name='\u0434\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0433\u043e \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u0441\u0442\u0430\u0442\u0443\u0441\u0430', blank=True)),
                ('decision_datetime', models.DateTimeField(null=True, verbose_name='\u0434\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f \u0432\u044b\u0434\u0435\u043b\u0435\u043d\u0438\u044f \u043c\u0435\u0441\u0442\u0430', blank=True)),
                ('distribution_datetime', models.DateTimeField(null=True, verbose_name='\u0434\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f \u043e\u043a\u043e\u043d\u0447\u0430\u0442\u0435\u043b\u044c\u043d\u043e\u0433\u043e \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u044f', blank=True)),
                ('distribute_in_any_sadik', models.BooleanField(default=True, help_text='\u0423\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u0435 \u044d\u0442\u043e\u0442 \u0444\u043b\u0430\u0433, \u0435\u0441\u043b\u0438 \u0433\u043e\u0442\u043e\u0432\u044b \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c\n            \u043c\u0435\u0441\u0442\u043e \u0432 \u043b\u044e\u0431\u043e\u043c \u0434\u0435\u0442\u0441\u043a\u043e\u043c \u0441\u0430\u0434\u0443 \u0432 \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0445 \u0442\u0435\u0440\u0440\u0438\u0442\u043e\u0440\u0438\u0430\u043b\u044c\u043d\u044b\u0445 \u043e\u0431\u043b\u0430\u0441\u0442\u044f\u0445,\n            \u0432 \u0441\u043b\u0443\u0447\u0430\u0435, \u043a\u043e\u0433\u0434\u0430 \u0432 \u043f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442\u043d\u044b\u0445 \u0414\u041e\u0423 \u043d\u0435 \u043e\u043a\u0430\u0436\u0435\u0442\u0441\u044f \u043c\u0435\u0441\u0442\u0430', verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0441\u043e\u0433\u043b\u0430\u0441\u0435\u043d \u043d\u0430 \u0437\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u0435 \u0432 \u0414\u041e\u0423, \u043e\u0442\u043b\u0438\u0447\u043d\u044b\u0435 \u043e\u0442 \u043f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442\u043d\u044b\u0445, \u0432 \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0445 \u0442\u0435\u0440\u0440\u0438\u0442\u043e\u0440\u0438\u0430\u043b\u044c\u043d\u044b\u0445 \u043e\u0431\u043b\u0430\u0441\u0442\u044f\u0445')),
                ('areas', models.ManyToManyField(help_text='\u0413\u0440\u0443\u043f\u043f\u0430 \u0432 \u043a\u043e\u0442\u043e\u0440\u043e\u0439 \u0432\u044b \u0445\u043e\u0442\u0435\u043b\u0438 \u0431\u044b \u043f\u043e\u0441\u0435\u0449\u0430\u0442\u044c \u0414\u041e\u0423.', to='core.Area', verbose_name='\u041f\u0440\u0435\u0434\u043f\u043e\u0447\u0438\u0442\u0430\u0435\u043c\u044b\u0435 \u0433\u0440\u0443\u043f\u043f\u044b \u0414\u041e\u0423')),
                ('benefit_category', models.ForeignKey(verbose_name='\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u043b\u044c\u0433\u043e\u0442', to='core.BenefitCategory', null=True)),
                ('benefits', models.ManyToManyField(to='core.Benefit', verbose_name='\u041b\u044c\u0433\u043e\u0442\u044b', blank=True)),
            ],
            options={
                'ordering': ['-benefit_category__priority', 'registration_datetime', 'id'],
                'verbose_name': '\u0417\u0430\u044f\u0432\u043a\u0430 \u0432 \u043e\u0447\u0435\u0440\u0435\u0434\u0438',
                'verbose_name_plural': '\u0417\u0430\u044f\u0432\u043a\u0438 \u0432 \u043e\u0447\u0435\u0440\u0435\u0434\u0438',
            },
        ),
        migrations.CreateModel(
            name='Sadik',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u043f\u043e\u043b\u043d\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('short_name', models.CharField(max_length=255, verbose_name='\u043a\u043e\u0440\u043e\u0442\u043a\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('number', models.IntegerField(null=True, verbose_name='\u043d\u043e\u043c\u0435\u0440')),
                ('identifier', models.CharField(max_length=25, null=True, verbose_name='\u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440')),
                ('email', models.CharField(max_length=255, verbose_name='\u044d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u0430\u044f \u043f\u043e\u0447\u0442\u0430', blank=True)),
                ('site', models.CharField(max_length=255, null=True, verbose_name='\u0441\u0430\u0439\u0442', blank=True)),
                ('head_name', models.CharField(max_length=255, verbose_name='\u0424\u0418\u041e \u0434\u0438\u0440\u0435\u043a\u0442\u043e\u0440\u0430 (\u0437\u0430\u0432\u0435\u0434\u0443\u044e\u0449\u0435\u0439)')),
                ('phone', models.CharField(max_length=255, null=True, verbose_name='\u0442\u0435\u043b\u0435\u0444\u043e\u043d', blank=True)),
                ('cast', models.CharField(max_length=255, verbose_name='\u0442\u0438\u043f(\u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f) \u0414\u041e\u0423', blank=True)),
                ('tech_level', models.TextField(null=True, verbose_name='\u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043e\u0441\u043d\u0430\u0449\u0435\u043d\u043d\u043e\u0441\u0442\u044c', blank=True)),
                ('training_program', models.TextField(null=True, verbose_name='\u0443\u0447\u0435\u0431\u043d\u044b\u0435 \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u044b \u0434\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0433\u043e \u043e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u043d\u0438\u044f', blank=True)),
                ('route_info', models.ImageField(upload_to='upload/sadiki/routeinfo/', null=True, verbose_name='\u0441\u0445\u0435\u043c\u0430 \u043f\u0440\u043e\u0435\u0437\u0434\u0430', blank=True)),
                ('extended_info', models.TextField(null=True, verbose_name='\u0434\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f', blank=True)),
                ('active_registration', models.BooleanField(default=True, verbose_name='\u043c\u043e\u0436\u0435\u0442 \u0431\u044b\u0442\u044c \u0443\u043a\u0430\u0437\u0430\u043d \u043a\u0430\u043a \u043f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442\u043d\u044b\u0439')),
                ('active_distribution', models.BooleanField(default=True, verbose_name='\u043f\u0440\u0438\u043d\u0438\u043c\u0430\u0435\u0442 \u0443\u0447\u0430\u0441\u0442\u0438\u0435 \u0432 \u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0438')),
                ('address', models.ForeignKey(verbose_name='\u0410\u0434\u0440\u0435\u0441', to='core.Address')),
                ('age_groups', models.ManyToManyField(to='core.AgeGroup', verbose_name='\u0412\u043e\u0437\u0440\u0430\u0441\u0442\u043d\u044b\u0435 \u0433\u0440\u0443\u043f\u043f\u044b')),
                ('area', models.ForeignKey(verbose_name='\u0413\u0440\u0443\u043f\u043f\u0430 \u0414\u041e\u0423', to='core.Area')),
            ],
            options={
                'ordering': ['number'],
                'verbose_name': '\u0414\u041e\u0423',
                'verbose_name_plural': '\u0414\u041e\u0423',
            },
        ),
        migrations.CreateModel(
            name='SadikGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('other_name', models.CharField(max_length=100, null=True, verbose_name='\u0410\u043b\u044c\u0442\u0435\u0440\u043d\u0430\u0442\u0438\u0432\u043d\u043e\u0435 \u0438\u043c\u044f', blank=True)),
                ('cast', models.IntegerField(default=0, verbose_name='\u0442\u0438\u043f', choices=[(0, '\u041e\u0431\u044b\u0447\u043d\u0430\u044f'), (1, '\u041a\u043e\u0440\u0440\u0435\u043a\u0446\u0438\u043e\u043d\u043d\u0430\u044f')])),
                ('capacity', models.PositiveIntegerField(default=0, verbose_name='\u043d\u043e\u043c\u0438\u043d\u0430\u043b\u044c\u043d\u0430\u044f \u0432\u043c\u0435\u0441\u0442\u0438\u043c\u043e\u0441\u0442\u044c')),
                ('free_places', models.PositiveIntegerField(default=0, verbose_name='\u043a\u043e\u043b-\u0432\u043e \u0441\u0432\u043e\u0431\u043e\u0434\u043d\u044b\u0445 \u043c\u0435\u0441\u0442')),
                ('min_birth_date', models.DateField(verbose_name='\u041d\u0430\u0438\u043c\u0435\u043d\u044c\u0448\u0438\u0439 \u0432\u043e\u0437\u0440\u0430\u0441\u0442')),
                ('max_birth_date', models.DateField(verbose_name='\u041d\u0430\u0438\u0431\u043e\u043b\u044c\u0448\u0438\u0439 \u0432\u043e\u0437\u0440\u0430\u0441\u0442')),
                ('year', models.DateField(verbose_name='\u0413\u043e\u0434 \u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f')),
                ('active', models.BooleanField(default=True, help_text='\u0415\u0441\u043b\u0438 \u0433\u0440\u0443\u043f\u043f\u0430 \u0430\u043a\u0442\u0438\u0432\u043d\u0430, \u0442\u043e \u0432 \u043d\u0435\u0451 \u043c\u043e\u0436\u043d\u043e \u0437\u0430\u0447\u0438\u0441\u043b\u044f\u0442\u044c \u0434\u0435\u0442\u0435\u0439', verbose_name='\u0410\u043a\u0442\u0438\u0432\u043d\u0430')),
                ('age_group', models.ForeignKey(blank=True, to='core.AgeGroup', null=True)),
            ],
            options={
                'ordering': ['-min_birth_date'],
                'verbose_name': '\u0420\u0430\u0441\u0447\u0451\u0442\u043d\u0430\u044f \u0433\u0440\u0443\u043f\u043f\u0430 \u0434\u0435\u0442\u0441\u043a\u043e\u0433\u043e \u0441\u0430\u0434\u0430',
                'verbose_name_plural': '\u0420\u0430\u0441\u0447\u0451\u0442\u043d\u044b\u0435 \u0433\u0440\u0443\u043f\u043f\u044b \u0434\u0435\u0442\u0441\u043a\u043e\u0433\u043e \u0441\u0430\u0434\u0430',
            },
        ),
        migrations.CreateModel(
            name='Vacancies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(null=True, verbose_name='\u0441\u0442\u0430\u0442\u0443\u0441', choices=[(None, '\u041c\u0435\u0441\u0442\u043e \u0441\u0432\u043e\u0431\u043e\u0434\u043d\u043e'), (0, '\u0412\u044b\u0434\u0435\u043b\u0435\u043d\u043e \u043c\u0435\u0441\u0442\u043e'), (4, '\u041d\u0430 \u0440\u0443\u0447\u043d\u043e\u043c \u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0438'), (5, '\u041f\u0435\u0440\u0435\u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0430 \u0432\u0440\u0443\u0447\u043d\u0443\u044e'), (1, '\u0417\u0430\u0447\u0438\u0441\u043b\u0435\u043d\u0430'), (2, '\u041e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u0435\u0442 \u043f\u043e \u0443\u0432\u0430\u0436\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0439 \u043f\u0440\u0438\u0447\u0438\u043d\u0435'), (3, '\u0412\u0440\u0435\u043c\u0435\u043d\u043d\u0430\u044f \u043f\u0443\u0442\u0435\u0432\u043a\u0430'), (6, '\u041c\u0435\u0441\u0442\u043e \u043d\u0435 \u0431\u044b\u043b\u043e \u043d\u0438\u043a\u043e\u043c\u0443 \u0432\u044b\u0434\u0435\u043b\u0435\u043d\u043e')])),
                ('distribution', models.ForeignKey(blank=True, to='core.Distribution', null=True)),
                ('sadik_group', models.ForeignKey(to='core.SadikGroup')),
            ],
        ),
        migrations.CreateModel(
            name='ChunkCustom',
            fields=[
            ],
            options={
                'verbose_name': '\u0411\u043b\u043e\u043a \u043d\u0430 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0435',
                'proxy': True,
                'verbose_name_plural': '\u0411\u043b\u043e\u043a\u0438 \u043d\u0430 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0435',
            },
            bases=('chunks.chunk',),
        ),
        migrations.AddField(
            model_name='sadikgroup',
            name='distributions',
            field=models.ManyToManyField(to='core.Distribution', through='core.Vacancies'),
        ),
        migrations.AddField(
            model_name='sadikgroup',
            name='sadik',
            field=models.ForeignKey(related_name='groups', to='core.Sadik'),
        ),
        migrations.AddField(
            model_name='requestion',
            name='closest_kg',
            field=models.ForeignKey(related_name='closest_kg', verbose_name='\u0411\u043b\u0438\u0436\u0430\u0439\u0448\u0438\u0439 \u0414\u041e\u0423', blank=True, to='core.Sadik', null=True),
        ),
        migrations.AddField(
            model_name='requestion',
            name='distributed_in_vacancy',
            field=models.ForeignKey(blank=True, to='core.Vacancies', null=True),
        ),
        migrations.AddField(
            model_name='requestion',
            name='district',
            field=models.ForeignKey(verbose_name='\u0420\u0430\u0439\u043e\u043d \u0437\u0430\u044f\u0432\u043a\u0438', blank=True, to='core.District', null=True),
        ),
        migrations.AddField(
            model_name='requestion',
            name='pref_sadiks',
            field=models.ManyToManyField(to='core.Sadik'),
        ),
        migrations.AddField(
            model_name='requestion',
            name='previous_distributed_in_vacancy',
            field=models.ForeignKey(related_name='previous_requestions', blank=True, to='core.Vacancies', null=True),
        ),
        migrations.AddField(
            model_name='requestion',
            name='profile',
            field=models.ForeignKey(verbose_name='\u041f\u0440\u043e\u0444\u0438\u043b\u044c \u0437\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u044f', to='core.Profile'),
        ),
        migrations.AddField(
            model_name='profile',
            name='sadiks',
            field=models.ManyToManyField(to='core.Sadik', null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='personaldocument',
            name='profile',
            field=models.ForeignKey(verbose_name='\u041f\u0440\u043e\u0444\u0438\u043b\u044c \u0437\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u044f', to='core.Profile'),
        ),
        migrations.AlterUniqueTogether(
            name='evidiencedocumenttemplate',
            unique_together=set([('name', 'destination')]),
        ),
        migrations.AddField(
            model_name='evidiencedocument',
            name='template',
            field=models.ForeignKey(verbose_name='\u0448\u0430\u0431\u043b\u043e\u043d \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430', to='core.EvidienceDocumentTemplate'),
        ),
        migrations.AddField(
            model_name='benefit',
            name='category',
            field=models.ForeignKey(verbose_name='\u0442\u0438\u043f \u043b\u044c\u0433\u043e\u0442', to='core.BenefitCategory'),
        ),
        migrations.AddField(
            model_name='benefit',
            name='evidience_documents',
            field=models.ManyToManyField(to='core.EvidienceDocumentTemplate', verbose_name='\u041d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u044b\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b'),
        ),
        migrations.AddField(
            model_name='benefit',
            name='sadik_related',
            field=models.ManyToManyField(to='core.Sadik', null=True, verbose_name='\u0414\u041e\u0423 \u0432 \u043a\u043e\u0442\u043e\u0440\u044b\u0445 \u0435\u0441\u0442\u044c \u0433\u0440\u0443\u043f\u043f\u044b', blank=True),
        ),
        migrations.AddField(
            model_name='area',
            name='district',
            field=models.ForeignKey(verbose_name='\u0420\u0430\u0439\u043e\u043d', blank=True, to='core.District', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='personaldocument',
            unique_together=set([('doc_type', 'series', 'number')]),
        ),
    ]
