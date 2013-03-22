# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.http import Http404
from django.utils import simplejson
from django.views.generic.base import TemplateView
from sadiki.core.models import Vacancies, Distribution, AgeGroup, Requestion, \
    STATUS_REQUESTER, STATUS_DECISION, STATUS_DISTRIBUTED, \
    VACANCY_STATUS_PROVIDED, VACANCY_STATUS_DISTRIBUTED, DISTRIBUTION_STATUS_END
from sadiki.core.utils import get_current_distribution_year
from sadiki.operator.views.base import OperatorPermissionMixin
from sadiki.statistics.models import StatisticsArchive, DECISION_STATISTICS, \
    DISTRIBUTION_STATISTICS
import datetime


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
                status=VACANCY_STATUS_PROVIDED).count()
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
                status=VACANCY_STATUS_PROVIDED).count()
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
            context = simplejson.loads(statistic_record.data)
        context.update({'current_year': year, 'years': years})
        return self.render_to_response(context)


class DecisionStatistics(Statistics):
    template_name = "statistics/decision_statistics.html"
    record_type = DECISION_STATISTICS


class DistributionStatistics(Statistics):
    template_name = "statistics/distribution_statistics.html"
    record_type = DISTRIBUTION_STATISTICS


class WaitTimeStatistics(TemplateView):
    template_name = 'statistics/wait_time_statistics.html'

    def get(self, request):
        requestions = Requestion.objects.all()
        max_child_age_months = settings.MAX_CHILD_AGE * 12
        current_datetime = datetime.datetime.now()
        groups = [{"name": age_group.name, 'min_birth_date': age_group.min_birth_date(),
            'max_birth_date': age_group.max_birth_date(), } for age_group
                in AgeGroup.objects.all()]
        if groups:
        #    добавляем самую малдшую возрастную группу
            small_group = {'name': '0-1 год', 'max_birth_date': datetime.date.today(),
                          'min_birth_date': groups[0]['max_birth_date']}
            groups.insert(0, small_group)
        wait_intervals = []
        from_months = 0
        for months in xrange(3, max_child_age_months + 1, 3):
            interval = {'name': '%s-%s' % (from_months, months - 1),
                        'from_months': from_months, 'to_months': months, }
            wait_intervals.append(interval)
            from_months = months
    #    добавляем дополнительный интервал итого
#        wait_intervals.append({'name': u'Итого', 'from_months': 0,
#                               'to_months': max_child_age_months})
        requestions_numbers_by_groups = []
        distributed_requestions_numbers_by_groups = []
        total_requestions_numbers_by_groups = [0 for group in groups]
    #    проходим по всем интервалам времени ожидания
        for interval in wait_intervals:
            from_months = interval['from_months']
            to_months = interval['to_months']
            requestions_numbers = []
            distributed_requestions_numbers = []
    #        добавляем в список интервал
    #        пробегаемся по группам и определяем кол-во заявок
            for i, group in enumerate(groups):
                delta = relativedelta(
                    current_datetime.date(), group['max_birth_date'])
    #            если для данной возрастной группы не может быть такого времени ожидания
                if from_months > delta.years * 12 + delta.months:
                    requestions_numbers.append(None)
                    distributed_requestions_numbers.append(None)
                else:
    #                подсчтиываем кол-во заявок в очереди для данной группы и для данного интервала
                    requestions_for_group = requestions.filter_for_age(
                        min_birth_date=group['min_birth_date'],
                        max_birth_date=group['max_birth_date'])
                    requestions_number = requestions_for_group.filter(
                        Q(registration_datetime__lte=current_datetime -
                                                     relativedelta(months=from_months)) &
                        Q(registration_datetime__gt=current_datetime -
                                                    relativedelta(months=to_months)),
                        status=STATUS_REQUESTER).count()
                    requestions_numbers.append(requestions_number)
#                    для группы прибавляем общее кол-во заявок в ней
                    total_requestions_numbers_by_groups[i] += requestions_number
    #                кол-во распределенных заявок
                    distributed_requestions_number = requestions_for_group.filter(
                        Q(registration_datetime__lte=F(
                            'distributed_in_vacancy__distribution__end_datetime') +
                                                     datetime.timedelta(days= -30 * from_months)) &
                        Q(registration_datetime__gt=F(
                            'distributed_in_vacancy__distribution__end_datetime') +
                                                    datetime.timedelta(days= -30 * to_months)),
                        status__in=(STATUS_DECISION, STATUS_DISTRIBUTED)).count()
                    distributed_requestions_numbers.append(distributed_requestions_number)
    #        для данного интервала список кол-ва заявок по группам
            requestions_numbers_by_groups.append(requestions_numbers)
            distributed_requestions_numbers_by_groups.append(distributed_requestions_numbers)
        total_requestions_number = sum(total_requestions_numbers_by_groups)
        return self.render_to_response({
            'requestions_numbers_by_groups':requestions_numbers_by_groups,
            'total_requestions_numbers_by_groups': total_requestions_numbers_by_groups,
            'wait_intervals': wait_intervals,
            'groups':groups,
            'total_requestions_number': total_requestions_number,
            'json': {
                'requestions_numbers_by_groups': simplejson.dumps(requestions_numbers_by_groups),
                'distributed_requestions_numbers_by_groups': simplejson.dumps(distributed_requestions_numbers_by_groups),
                'wait_intervals': simplejson.dumps(wait_intervals),
                },
            })
