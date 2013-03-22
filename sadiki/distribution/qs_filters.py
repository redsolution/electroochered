# -*- coding: utf-8 -*-
from sadiki.core.utils import get_current_distribution_year
from sadiki.distribution.models import Queue, QuerySetFilter


class AgeQuerySetFilter(QuerySetFilter):
    u"""Фильтрует заявки по возрастной категории"""

    def get_filter_dict(self):
        return {
            'birth_date__gt': self.age_group.min_birth_date(),
            'birth_date__lte': self.age_group.max_birth_date(),
        }

class DistributuionYearQuerySetFilter(QuerySetFilter):
    u"""Убирает заявки, которые не хотят в этом году получать место"""

    def get_filter_dict(self):
        return {
            'admission_date__year__lte': get_current_distribution_year().year,
            'admission_date__isnull': True,
        }


class QueueByAge(Queue):
    u"""
    Очередь на комплектование по возрастным категориям

    Использовать так:

        QueueByAge(distribution, {'age_group': age_group}, ...)
    """

    def __init__(self, distribution, age_group, **kwds):
        self.age_group = age_group
        kwds['age_group'] = age_group
        kwds['queryset_filter_classes'] = [AgeQuerySetFilter]
        super(QueueByAge, self).__init__(distribution, **kwds)

    @property
    def vacancies(self):
        vacancies = super(QueueByAge, self).vacancies
        return vacancies.filter(
            sadik_group__age_group=self.age_group).all()

