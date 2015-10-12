# -*- coding: utf-8 -*-
import sys
import traceback

from django.contrib.auth.models import User
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db.models import F

from sadiki.core.models import Distribution, STATUS_ON_DISTRIBUTION, \
    Requestion, DISTRIBUTION_STATUS_END, STATUS_ON_TEMP_DISTRIBUTION, \
    VACANCY_STATUS_DISTRIBUTED, VACANCY_STATUS_MANUALLY_CHANGED, \
    VACANCY_STATUS_MANUALLY_DISTRIBUTING, VACANCY_STATUS_PROVIDED, Vacancies, \
    STATUS_DECISION, DISTRIBUTION_STATUS_ENDING, SadikGroup, \
    VACANCY_STATUS_NOT_PROVIDED
import datetime
from sadiki.logger.models import Logger


class Command(BaseCommand):
    help_text = '''Usage: manage.py auto_distribution'''
    args = ['username']

    def handle(self, *args, **options):
        from sadiki.core.workflow import VACANCY_DISTRIBUTED
        user = User.objects.get(username=args[0])
        try:
            distribution = Distribution.objects.get(
                status=DISTRIBUTION_STATUS_ENDING)
        except:
            pass
        else:
            try:
                # все нераспределенные заявки возвращаются в очередь
                Requestion.objects.filter(status=STATUS_ON_DISTRIBUTION).update(
                    status=F('previous_status'))
                Requestion.objects.filter(
                    status=STATUS_ON_TEMP_DISTRIBUTION).update(
                    status=F('previous_status'))
                # для всех путевок выставляется статус распределенных
                for vacancy in distribution.vacancies_set.filter(
                        status__in=(
                            VACANCY_STATUS_PROVIDED,
                            VACANCY_STATUS_MANUALLY_DISTRIBUTING,
                            VACANCY_STATUS_MANUALLY_CHANGED)
                ).select_related('sadik_group__sadik'):
                    requestion = vacancy.requestion_set.get(
                        status=STATUS_DECISION)
                    # записываем в логи информацию о изменении статуса
                    # заявки(также должна высылаться почта)
                    Logger.objects.create_for_action(
                        VACANCY_DISTRIBUTED,
                        context_dict={'sadik': vacancy.sadik_group.sadik},
                        extra={'user': user, 'obj': requestion,
                               'vacancy': vacancy, })
                SadikGroup.objects.active().update(free_places=0, capacity=0)
                distribution.status = DISTRIBUTION_STATUS_END
                distribution.end_datetime = datetime.datetime.now()
                distribution.save()
                Vacancies.objects.filter(
                    distribution=distribution, status__isnull=True).update(
                    status=VACANCY_STATUS_NOT_PROVIDED)
            except Exception:
                ex_type, ex, tb = sys.exc_info()
                message = u""
                for item in traceback.format_exception(ex_type, ex, tb):
                    message += item
                message += u"/nОператор: {}".format(user)
                mail_admins('Distribution error', message)
