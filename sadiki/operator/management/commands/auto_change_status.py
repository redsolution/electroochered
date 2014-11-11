# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand
from sadiki.core.models import STATUS_NOT_APPEAR, STATUS_ABSENT, Requestion, \
    STATUS_ABSENT_EXPIRE, STATUS_NOT_APPEAR_EXPIRE
from sadiki.logger.models import Logger
import datetime
from sadiki.core.workflow import ABSENT_EXPIRE


class Command(BaseCommand):
    help = u"Для заявок у которых истек срок обжалования изменяет статус"

    def handle(self, *args, **options):
        expiration_datetime = datetime.datetime.now() - datetime.timedelta(
            days=settings.APPEAL_DAYS)
        print "NOT_APPEAR_TRANSITION expired since 1.6.3 version"
        for requestion in Requestion.objects.filter(status=STATUS_ABSENT,
            status_change_datetime__lte=expiration_datetime):
            requestion.status = STATUS_ABSENT_EXPIRE
            requestion.save()
            Logger.objects.create_for_action(ABSENT_EXPIRE,
                extra={'user': None, 'obj': requestion})