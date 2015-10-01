# -*- coding: utf-8 -*-
import datetime
import json

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.http import Http404
from django.views.generic.base import TemplateView
from sadiki.core.models import Vacancies, Distribution, AgeGroup, Requestion, \
    STATUS_REQUESTER, STATUS_DECISION, STATUS_DISTRIBUTED, \
    VACANCY_STATUS_PROVIDED, VACANCY_STATUS_DISTRIBUTED, DISTRIBUTION_STATUS_END
from sadiki.core.permissions import RequirePermissionsMixin
from sadiki.core.utils import get_current_distribution_year
from sadiki.operator.views.base import OperatorPermissionMixin
from sadiki.statistics.models import StatisticsArchive, DECISION_STATISTICS, \
    DISTRIBUTION_STATISTICS


def get_decision_statistics_data():
    statistic = []
    distribution_year = get_current_distribution_year()
    distributions = Distribution.objects.filter(
        year__year=distribution_year.year, status=DISTRIBUTION_STATUS_END)

    context = {'distributions_names': [distribution.start_datetime.date()
        for distribution in distributions]}
    age_groups = AgeGroup.objects.all()
    total = [{'free_places_before':0, 'places_decision':0} for age_group
        in age_groups]
    context.update({'age_groups_names': [age_group.name for age_group
                                            in age_groups]})
#    проходимся по всем распределениям
    for distribution in distributions:
        distribution_data = []
#                выборка статистики по возрастным группам
        for i, age_group in enumerate(age_groups):
            vacancies = Vacancies.objects.filter(
                distribution=distribution, sadik_group__age_group=age_group)
            free_places_before = vacancies.count()
            places_decision = vacancies.filter(
                status__in=(VACANCY_STATUS_PROVIDED, VACANCY_STATUS_DISTRIBUTED)).count()
            distribution_data.append(
                    {'free_places_before': free_places_before,
                     'places_decision': places_decision})
            total[i]['free_places_before'] += free_places_before
            total[i]['places_decision'] += places_decision
            # Накопление итогов
        statistic.append(distribution_data)
#    добавляем данные об общем количестве
    statistic.append(total)
    context.update({'statistic': statistic})
    return context


def get_distribution_statistics_data():
    statistic = []
    distribution_year = get_current_distribution_year()
    distributions = Distribution.objects.filter(
        year__year=distribution_year.year)
    context = {'distributions_names': [distribution.start_datetime.date()
        for distribution in distributions]}
    age_groups = AgeGroup.objects.all()
    total = [{'number_of_distributed':0, 'places_decision':0}
        for age_group in age_groups]
    context.update({'age_groups_names': [age_group.name for age_group
                                            in age_groups]})
    #            проходимся по всем распределениям
    for distribution in distributions:
        distribution_data = []
        #                выборка статистики по возрастным группам
        for i, age_group in enumerate(age_groups):
            vacancies = Vacancies.objects.filter(
                distribution=distribution, sadik_group__age_group=age_group)
            places_decision = vacancies.filter(
                status__in=(VACANCY_STATUS_PROVIDED, VACANCY_STATUS_DISTRIBUTED)).count()
            number_of_distributed = vacancies.filter(
                status=VACANCY_STATUS_DISTRIBUTED).count()
            distribution_data.append(
                    {'number_of_distributed': number_of_distributed,
                     'places_decision': places_decision})
            total[i]['number_of_distributed'] += number_of_distributed
            total[i]['places_decision'] += places_decision
            # Накопление итогов
        statistic.append(distribution_data)
#            добавляем данные об общем количестве
    statistic.append(total)
    context.update({'statistic': statistic})
    return context

STATISTIC_HANDLER_FOR_TYPE = {
    DECISION_STATISTICS: get_decision_statistics_data,
    DISTRIBUTION_STATISTICS: get_distribution_statistics_data,
    }


class Statistics(OperatorPermissionMixin, TemplateView):
    record_type = None

    def get(self, request, year=None):
        current_distribution_year = get_current_distribution_year().year
        years = [year_date.year for year_date in StatisticsArchive.objects.filter(
            record_type=self.record_type).order_by('year').dates('year', 'year')]
        if current_distribution_year not in years:
            years = [current_distribution_year, ] + years
        if not year:
            year = current_distribution_year
        else:
            year = int(year)
        if year not in years:
            raise Http404
        if year == current_distribution_year:
            context = STATISTIC_HANDLER_FOR_TYPE[self.record_type]()
        else:
            statistic_record = StatisticsArchive.objects.filter(
                record_type=DECISION_STATISTICS, year__year=year)[0]
            context = json.loads(statistic_record.data)
        context.update({'current_year': year, 'years': years})
        return self.render_to_response(context)


class DecisionStatistics(Statistics):
    template_name = "statistics/decision_statistics.html"
    record_type = DECISION_STATISTICS


class DistributionStatistics(Statistics):
    template_name = "statistics/distribution_statistics.html"
    record_type = DISTRIBUTION_STATISTICS


class WaitTimeStatistics(RequirePermissionsMixin, TemplateView):
    template_name = 'statistics/wait_time_statistics.html'
