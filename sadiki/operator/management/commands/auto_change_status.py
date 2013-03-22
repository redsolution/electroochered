# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand
from sadiki.core.models import STATUS_NOT_APPEAR, STATUS_ABSENT, Requestion, \
    STATUS_ABSENT_EXPIRE, STATUS_NOT_APPEAR_EXPIRE
from sadiki.logger.models import Logger
import datetime
from sadiki.core.workflow import NOT_APPEAR_EXPIRE, ABSENT_EXPIRE


class Command(BaseCommand):
    help = u"Для заявок у которых истек срок обжалования изменяет статус"

    def handle(self, *args, **options):
        expiration_datetime = datetime.datetime.now() - datetime.timedelta(
            days=settings.APPEAL_DAYS)
        for requestion in Requestion.objects.filter(status=STATUS_NOT_APPEAR,
            status_change_datetime__lte=expiration_datetime):
            requestion.status = STATUS_NOT_APPEAR_EXPIRE
            Logger.objects.create_for_action(NOT_APPEAR_EXPIRE,
                extra={'user': None, 'obj': requestion})
        for requestion in Requestion.objects.filter(status=STATUS_ABSENT,
            status_change_datetime__lte=expiration_datetime):
            requestion.status = STATUS_ABSENT_EXPIRE
            Logger.objects.create_for_action(ABSENT_EXPIRE,
                extra={'user': None, 'obj': requestion})

