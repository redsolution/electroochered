# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from sadiki.core.models import Distribution, \
    STATUS_ON_DISTRIBUTION, Requestion, DISTRIBUTION_STATUS_END, STATUS_REQUESTER, STATUS_ON_TEMP_DISTRIBUTION, STATUS_TEMP_DISTRIBUTED, VACANCY_STATUS_DISTRIBUTED, VACANCY_STATUS_MANUALLY_CHANGED, VACANCY_STATUS_MANUALLY_DISTRIBUTING, VACANCY_STATUS_PROVIDED, Vacancies, STATUS_DECISION, DISTRIBUTION_STATUS_ENDING, SadikGroup, VACANCY_STATUS_NOT_PROVIDED
import datetime
from sadiki.logger.models import Logger
from optparse import make_option


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
#            все нераспределенные заявки возвращаются в очередь
            Requestion.objects.filter(status=STATUS_ON_DISTRIBUTION).update(
                status=STATUS_REQUESTER)
            Requestion.objects.filter(status=STATUS_ON_TEMP_DISTRIBUTION
                ).update(status=STATUS_TEMP_DISTRIBUTED)
#            для всех путевок выставляется статус распределенных
            for vacancy in distribution.vacancies_set.filter(
                    status__in=(VACANCY_STATUS_PROVIDED,
                    VACANCY_STATUS_MANUALLY_DISTRIBUTING,
                    VACANCY_STATUS_MANUALLY_CHANGED)).select_related('sadik'):
                requestion = vacancy.requestion_set.get(status=STATUS_DECISION)
#                записываем в логи информацию о изменении статуса заявки(также должна высылаться почта)
                Logger.objects.create_for_action(VACANCY_DISTRIBUTED,
                    context_dict={'sadik': vacancy.sadik_group.sadik},
                    extra={'user': user, 'obj': requestion,
                           'vacancy': vacancy, })
            SadikGroup.objects.active().update(free_places=0, capacity=0)
            distribution.status = DISTRIBUTION_STATUS_END
            distribution.end_datetime = datetime.datetime.now()
            distribution.save()
            Vacancies.objects.filter(distribution=distribution, status__isnull=True).update(
                status=VACANCY_STATUS_NOT_PROVIDED)
