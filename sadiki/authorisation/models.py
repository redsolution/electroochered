# -*- coding: utf-8 -*-
import hashlib

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import render_to_string
from sadiki.core.utils import scheme_and_domain
from settings import VERIFICATION_KEY_DAYS
import datetime
import random


class VerificationKeyManager(models.Manager):
    def create_key(self, user):
        u"""В базе данных создается новый ключ для пользователя"""
        while True:
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            key = hashlib.sha1(salt + user.username).hexdigest()
            try:
                self.get_query_set().get(key=key)
            except self.model.DoesNotExist:
                break

        email_key = self.model(user=user, key=key)
        email_key.save()
        return email_key


class VerificationKey(models.Model):
    u"""
    Хранение ключей содержащихся в ссылках, отправляемых на e-mail
    (восстановление пароля, подтверждение адреса элкетронной почты)
    """
    user = models.ForeignKey(User)
    key = models.CharField(max_length=40, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    unused = models.BooleanField(verbose_name=u'ключ не использовался',
        default=True)

    objects = VerificationKeyManager()

    @property
    def is_expired(self):
        return (datetime.datetime.now() - self.created).days > VERIFICATION_KEY_DAYS

    @property
    def is_valid(self):
        if not self.is_expired and self.unused:
            return True
        else:
            return False

    def send_email(self, subject, template, context):
        context.update({'user': self.user, 'VERIFICATION_KEY_DAYS': VERIFICATION_KEY_DAYS})
        context.update(scheme_and_domain())
        message = render_to_string(template, context)
        return send_mail(subject=subject,
            message=message,
            from_email=None,
            recipient_list=[self.user.email, ])

    def send_email_verification(self, password=None):
        u"""Отправка сообщения пользователю о подтверждении e-mail"""
        context = {
            'url': reverse('email_verification', args=[self.key]),
            'password': password
            }
        self.send_email(u'Регистрация на сайте',
            'authorisation/emails/registration.txt',
            context)

    def send_email_change(self, password=None):
        u"""Отправка сообщения при изменении e-mail адреса"""
        context = {
            'url': reverse('email_verification', args=[self.key]),
            'password': password,
        }
        self.send_email(u'Изменение адреса электронной почты',
            'authorisation/emails/email_change.txt',
            context)

    def send_reset_password(self):
        u"""Отправка сообщения пользователю о сбросе пароля"""
        context = {
            'url': reverse('reset_password', args=[self.key])
            }
        self.send_email(u'Сброс пароля',
            'authorisation/emails/recovery_password.txt', context)

