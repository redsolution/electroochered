# -*- coding: utf-8 -*-
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from sadiki.core.utils import get_current_distribution_year
import json

DECISION_STATISTICS = 0
DISTRIBUTION_STATISTICS = 1
WAITE_TIME_STATISTICS = 2
STATISTIC_TYPE_CHOICES = (
    (DECISION_STATISTICS, u"Статистика распределения мест"),
    (DISTRIBUTION_STATISTICS, u"Статистика зачисления"),
    (WAITE_TIME_STATISTICS, u"Статистика времени ожидания в очереди"),
    )


class StatisticsArchiveQuerySet(models.query.QuerySet):

    def create_statistic_record(self, type):
        from sadiki.statistics.views import STATISTIC_HANDLER_FOR_TYPE
        data = json.dumps(STATISTIC_HANDLER_FOR_TYPE[type](), cls=DjangoJSONEncoder)
        year = get_current_distribution_year()
        statistic_record = self.create(record_type=type,
            data=data, year=year)
        return statistic_record


class StatisticsArchive(models.Model):
    record_type = models.IntegerField(verbose_name=u"Тип статистики", choices=STATISTIC_TYPE_CHOICES)
    data = models.TextField(verbose_name=u"Данные статистики")
    date = models.DateField(verbose_name=u"Дата на которую актуальна статистика", auto_now_add=True)
    year = models.DateField(verbose_name=u"Год распределения к которому относится статистика")
    objects = StatisticsArchiveQuerySet.as_manager()

    def __unicode__(self):
        return u"%s за %d" % (self.get_record_type_display(), self.year.year)
