# -*- coding: utf-8 -*-
import datetime
import json

from dateutil.relativedelta import relativedelta
from django import template
from django.conf import settings
from django.db import connection
from sadiki.core.models import Requestion, STATUS_REQUESTER, \
    STATUS_ON_DISTRIBUTION, AgeGroup, STATUS_DISTRIBUTED, DISTRIBUTION_PROCESS_STATUSES
from sadiki.core.utils import get_current_distribution_year

register = template.Library()


@register.inclusion_tag("statistics/templatetags/wait_time_statistics_tag.html")
def show_wait_time_statistics():
    cursor = connection.cursor()
    max_child_age_months = settings.MAX_CHILD_AGE * 12
    current_datetime = datetime.datetime.now()
    current_distribution_year = get_current_distribution_year()
    groups = [{"name": age_group.name, 'short_name': age_group.short_name,
               'min_birth_date': age_group.min_birth_date(current_distribution_year),
               'max_birth_date': age_group.max_birth_date(current_distribution_year), } for age_group
              in AgeGroup.objects.all()]
    wait_intervals = []
    from_months = 0
    for months in xrange(3, max_child_age_months + 1, 3):
        interval = {'name': '%s-%s' % (from_months, months - 1),
                    'from_months': from_months, 'to_months': months, }
        wait_intervals.append(interval)
        from_months = months
    requestions_numbers_by_groups = []
    distributed_requestions_numbers_by_groups = []
    total_requestions_numbers_by_groups = [0] * len(groups)
    # проходим по всем интервалам времени ожидания
    for interval in wait_intervals:
        from_months = interval['from_months']
        to_months = interval['to_months']
        requestions_numbers = []
        distributed_requestions_numbers = []
        # пробегаемся по группам и определяем кол-во заявок
        registration_datetime_max = current_datetime - relativedelta(months=from_months)
        registration_datetime_min = current_datetime - relativedelta(months=to_months)
        for i, group in enumerate(groups):
            delta = relativedelta(
                current_datetime.date(), group['min_birth_date'])
            # если для данной возрастной группы не может быть такого времени ожидания
            if from_months > delta.years * 12 + delta.months or (from_months == delta.years * 12 + delta.months
                                                                 and delta.days == 0):
                requestions_numbers.append(None)
                distributed_requestions_numbers.append(None)
            else:
                # подсчитываем кол-во заявок в очереди для данной группы и для данного интервала
                cursor.execute("""SELECT COUNT(*) FROM "core_requestion"
                    WHERE ("core_requestion"."birth_date" > %(min_birth_date)s AND
                            "core_requestion"."birth_date" <= %(max_birth_date)s) AND
                        ("core_requestion"."registration_datetime" <= %(registration_datetime_max)s AND
                            "core_requestion"."registration_datetime" > %(registration_datetime_min)s) AND
                        "core_requestion"."status" IN %(statuses)s
                    """, {"min_birth_date": group["min_birth_date"], "max_birth_date": group["max_birth_date"],
                          "registration_datetime_max": registration_datetime_max,
                          "registration_datetime_min": registration_datetime_min,
                          "statuses": (STATUS_REQUESTER, STATUS_ON_DISTRIBUTION)})
                requestions_number = cursor.fetchone()[0]
                requestions_numbers.append(requestions_number)
                # для группы прибавляем общее кол-во заявок в ней
                total_requestions_numbers_by_groups[i] += requestions_number
                # кол-во распределенных заявок
                cursor.execute("""SELECT COUNT(*) FROM "core_requestion"
                    WHERE ("core_requestion"."birth_date" > %(min_birth_date)s AND
                            "core_requestion"."birth_date" <= %(max_birth_date)s) AND
                        ("core_requestion"."registration_datetime" <=
                                ("core_requestion"."decision_datetime" - interval '%(from_days)s months') AND
                            "core_requestion"."registration_datetime" >
                                ("core_requestion"."decision_datetime" - interval '%(to_days)s months')) AND
                        "core_requestion"."status" IN (13, 6, 9, 15, 54, 16, 53)
                    """, {"min_birth_date": group["min_birth_date"], "max_birth_date": group["max_birth_date"],
                          "from_days": from_months,
                          "to_days": to_months,
                          "statuses": (STATUS_DISTRIBUTED, ) + DISTRIBUTION_PROCESS_STATUSES})
                distributed_requestions_number = cursor.fetchone()[0]
                distributed_requestions_numbers.append(distributed_requestions_number)
        # для данного интервала список кол-ва заявок по группам
        requestions_numbers_by_groups.append(requestions_numbers)
        distributed_requestions_numbers_by_groups.append(distributed_requestions_numbers)
    total_requestions_number = sum(total_requestions_numbers_by_groups)
    return {
        'requestions_numbers_by_groups': requestions_numbers_by_groups,
        'total_requestions_numbers_by_groups': total_requestions_numbers_by_groups,
        'wait_intervals': wait_intervals,
        'groups': groups,
        'total_requestions_number': total_requestions_number,
        'json': {
            'requestions_numbers_by_groups': json.dumps(requestions_numbers_by_groups),
            'distributed_requestions_numbers_by_groups': json.dumps(distributed_requestions_numbers_by_groups),
            'wait_intervals': json.dumps(wait_intervals),
        },
    }


@register.inclusion_tag("statistics/templatetags/requestion_statistics.html")
def requestions_statistics():
    requestions = Requestion.objects.filter(status__in=(STATUS_REQUESTER,
                                                        STATUS_ON_DISTRIBUTION))
    age_groups = AgeGroup.objects.all()
    requestions_numbers_by_groups = []
    current_distribution_year = get_current_distribution_year()
    for group in age_groups:
        requestions_numbers_by_groups.append(
            requestions.filter_for_age(min_birth_date=group.min_birth_date(current_distribution_year),
                                       max_birth_date=group.max_birth_date(current_distribution_year)).count())
    context = {
        'requestions_number': requestions.count(),
        'benefit_requestions_number': requestions.filter(
            benefit_category__priority__gt=0).count(),
        'groups': age_groups,
        'requestions_numbers_by_groups': requestions_numbers_by_groups
    }
    return context
