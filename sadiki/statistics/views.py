# -*- coding: utf-8 -*-
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from sadiki.anonym.forms import SimpleFilterForm
from sadiki.core.models import Vacancies, Distribution, AgeGroup, Requestion, \
    STATUS_REQUESTER, STATUS_DISTRIBUTED, \
    VACANCY_STATUS_PROVIDED, VACANCY_STATUS_DISTRIBUTED, DISTRIBUTION_STATUS_END, DISTRIBUTION_PROCESS_STATUSES, STATUS_REQUESTER_NOT_CONFIRMED
from sadiki.core.permissions import RequirePermissionsMixin
from sadiki.core.utils import get_current_distribution_year
from sadiki.statistics.models import DECISION_STATISTICS, \
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


class WaitTimeStatistics(RequirePermissionsMixin, TemplateView):
    template_name = 'statistics/wait_time_statistics.html'


class RequestionsMap(RequirePermissionsMixin, TemplateView):
    template_name = 'statistics/requestions_map.html'

    def get_context_data(self, **kwargs):
        return {
            'params': kwargs,
            'form': SimpleFilterForm,
        }


@csrf_exempt
def requestions_coords_json(request):
    if request.is_ajax() and request.method == "POST":
        form = SimpleFilterForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            confirmed = cleaned_data.get("confirmed")
            age_group = cleaned_data.get("age_group")
            area = cleaned_data.get("area")
            queryset = Requestion.objects.queue().exclude(
                location__isnull=True).extra(select={"coords": "astext(location)"})
            if confirmed:
                queryset = queryset.confirmed()
            if age_group:
                queryset = queryset.filter_for_age(min_birth_date=age_group.min_birth_date(),
                                                   max_birth_date=age_group.max_birth_date())
            if form.cleaned_data.get('benefit_category', None):
                queryset = queryset.filter(benefit_category=form.cleaned_data['benefit_category'])
            if area:
                queryset = queryset.filter(
                    (Q(areas=area) |
                    Q(areas__isnull=True) | Q(pref_sadiks__area=area)) & Q(status__in=(STATUS_REQUESTER, STATUS_REQUESTER_NOT_CONFIRMED)) |(
                    Q(distributed_in_vacancy__sadik_group__sadik__area=area)
                    & Q(status__in=DISTRIBUTION_PROCESS_STATUSES+(STATUS_DISTRIBUTED,)))
                ).distinct()
            return HttpResponse(simplejson.dumps(list(queryset.values('requestion_number', 'coords'))),
                                mimetype='text/json')
    return