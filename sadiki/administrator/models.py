# -*- coding: utf-8 -*-
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Photo(models.Model):
    name = models.CharField(verbose_name=u'название', max_length=255)
    description = models.CharField(verbose_name=u'описание', max_length=255,
        blank=True, null=True)
    image = models.ImageField(verbose_name=u'фотография',
        upload_to='upload/sadik/images/', blank=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

