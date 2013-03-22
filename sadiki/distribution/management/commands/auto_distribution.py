# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from itertools import izip
from sadiki.core.models import Distribution, AgeGroup,\
    DISTRIBUTION_STATUS_INITIAL, DISTRIBUTION_STATUS_AUTO, DISTRIBUTION_STATUS_START, \
    STATUS_WANT_TO_CHANGE_SADIK, STATUS_ON_TEMP_DISTRIBUTION, STATUS_TEMP_DISTRIBUTED,\
    STATUS_ON_DISTRIBUTION, STATUS_REQUESTER, STATUS_ON_TRANSFER_DISTRIBUTION, Sadik, SadikGroup, Requestion
from sadiki.distribution.models import DataTable

from sadiki.distribution.qs_filters import QueueByAge
from sadiki.logger.models import Logger
import datetime


class Command(BaseCommand):
    help_text = '''Usage: manage.py auto_distribution'''

    def handle(self, *args, **options):
        from sadiki.core.workflow import DECISION, TRANSFER_APROOVED, PERMANENT_DECISION
        auto_distributions = Distribution.objects.filter(
            status=DISTRIBUTION_STATUS_AUTO)
        if auto_distributions.exists():
            distribution = auto_distributions[0]
            age_groups = AgeGroup.objects.all()


            for age_group in age_groups:

                while True:
                    queue_by_age = QueueByAge(distribution, age_group=age_group)

                    sadik_group_ids = queue_by_age.vacancies.all().values_list('sadik_group__id', flat=True)
                    sadik_groups = SadikGroup.objects.filter(id__in=sadik_group_ids)


                    table = DataTable(sadik_groups, list(queue_by_age.competitors()))
                    try:
                        row = table.row_groups[0][0]
                    except IndexError:
                        break
                    # Наименее востребованная и наиболее приоритетная группа

                    selected_cell = None
                    for cell in row:
                        if cell.weight and table.cols.get_col(cell.sadik_group).popularity:
                            factor = lambda cell: cell.weight / table.cols.get_col(cell.sadik_group).popularity
                            if selected_cell is None or factor(cell) < factor(selected_cell):
                                selected_cell = cell

                    if selected_cell:
                        requestion = row.instance
                        sadik_group = selected_cell.sadik_group
                    else:
                        break

                    # Зачисляем


                    if requestion.status == STATUS_REQUESTER:
                        requestion.status = STATUS_ON_DISTRIBUTION
                        requestion.save()
                        requestion.distribute_in_sadik_from_requester(sadik_group.sadik)
                        Logger.objects.create_for_action(DECISION, extra={'user': None, 'obj': requestion})

                    if requestion.status == STATUS_TEMP_DISTRIBUTED:
                        requestion.status = STATUS_ON_TEMP_DISTRIBUTION
                        requestion.save()
                        requestion.distribute_in_sadik_from_tempdistr(sadik_group.sadik)
                        Logger.objects.create_for_action(PERMANENT_DECISION, extra={'user': None, 'obj': requestion})

                    if requestion.status == STATUS_WANT_TO_CHANGE_SADIK:
                        requestion.status = STATUS_ON_TRANSFER_DISTRIBUTION
                        requestion.save()
                        requestion.distribute_in_sadik_from_sadikchange(sadik_group.sadik)
                        Logger.objects.create_for_action(TRANSFER_APROOVED, extra={'user': None, 'obj': requestion})

            distribution.status = DISTRIBUTION_STATUS_START
            distribution.save()

def test():
    initial_distributions = Distribution.objects.filter(
        status__in=(DISTRIBUTION_STATUS_INITIAL, DISTRIBUTION_STATUS_AUTO))

    if initial_distributions:
        distribution = initial_distributions[0]
        distribution.start_datetime = datetime.datetime.now()

        age_group = AgeGroup.objects.all()[0]
        queue_by_age = QueueByAge(distribution, age_group=age_group)
        sadik_group_ids = queue_by_age.vacancies.all().values_list('sadik_group__id', flat=True)
        sadik_groups = SadikGroup.objects.filter(id__in=sadik_group_ids)

        return DataTable(sadik_groups, list(queue_by_age.competitors()))
