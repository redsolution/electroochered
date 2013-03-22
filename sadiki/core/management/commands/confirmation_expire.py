# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from sadiki.core.models import Requestion, STATUS_REQUESTER_NOT_CONFIRMED, \
    STATUS_REJECTED
from sadiki.logger.models import Logger
import datetime
from sadiki.core.workflow import REQUESTION_REJECT


class Command(BaseCommand):
    help_text = '''Usage: manage.py confirmation_expire
    Set requestions with expired confirmation time to 
    '''

    def handle(self, *args, **options):
        expire_date = datetime.date.today() - relativedelta(
            months=settings.DOCUMENTS_VALID)
        for requestion in Requestion.objects.filter(
            status=STATUS_REQUESTER_NOT_CONFIRMED,
            registration_datetime__lt=expire_date
            ):
            if Requestion.objects.filter(
                    id=requestion.id,
                    status=STATUS_REQUESTER_NOT_CONFIRMED
                    ).update(status=STATUS_REJECTED):
                Logger.objects.create_for_action(REQUESTION_REJECT,
                    extra={'obj': requestion})
