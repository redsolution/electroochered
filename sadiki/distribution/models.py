# -*- coding: utf-8 -*-
from itertools import product, groupby
from django.db.models.query_utils import Q
from sadiki.core.models import Requestion, SadikGroup

CELL_WEIGHT = 100.0
POPULARITY_weight = 100.0


class Filter(object):
    """Base class for queue filters"""

    def __init__(self, distribution, **params):
        self.distribution = distribution
        for key, value in params.iteritems():
            setattr(self, key, value)

class QuerySetFilter(Filter):

    def get_filter_dict(self):
        u"""Нужно вернуть словарь или Q объект, который передастся аргументом к filter"""
        raise NotImplemented

class RuntimeFilter(Filter):

    def accept_requestion(self, requestion):
        u"""Если заявка подходит, возвращаем True"""
        raise NotImplemented

class Queue(object):
    u"""
    Класс для отбора заявок, между которыми будут распределяться места

    queryset_filter_classes - Фильтры Queryset заявок
    runtime_filters_classes - список объектов, которые определяют
        для каждой конкретной заявки, давать ей место или нет
    """
    qs_filters = None
    runtime_filters = None

    def __init__(self, distribution, queryset_filter_classes=None, runtime_filters_classes=None, **params):
        self.distribution = distribution

        self.qs_filters = []
        if queryset_filter_classes:
            for QSFilter in queryset_filter_classes:
                self.qs_filters.append(QSFilter(self.distribution, **params))

        self.runtime_filters = []
        if runtime_filters_classes:
            for RuntimeFilter in runtime_filters_classes:
                self.runtime_filters.append(RuntimeFilter(self.distribution, **params))

    @property
    def vacancies(self):
        return self.distribution.vacancies_set.filter(status__isnull=True)

    def competitors(self):
        u"""
        Возвращает итератор заявок, между которыми
        будут распределять места
        """
        queue = Requestion.objects.not_distributed()

        for filter in self.qs_filters:
            filter_dict = filter.get_filter_dict()
            if isinstance(filter_dict, Q):
                queue = queue.filter(filter_dict)
            else:
                queue = queue.filter(**filter_dict)
        length = self.vacancies.count()
        for i, requestion in enumerate(queue):
            if i < length:
                accept = True
                for filter in self.runtime_filters:
                    accept = accept and filter.accept_requestion(requestion)
                if accept:
                    yield requestion
                else:
                    continue
            else:
                break

# -----------------------------------------------------------------------
# |                 Таблицы автоматического распределения               |
# -----------------------------------------------------------------------

class Cell(object):
    u"""ячейка, отражающая возможность попадения заявки в садик"""

    def __init__(self, sadik_group, requestion):
        object.__init__(self)
        self.sadik_group = sadik_group
        self.requestion = requestion
        self.distance = self.get_distance()
        self.weight = 0

    def get_distance(self):
        sadik_coords = self.sadik_group.sadik.address.coords
        child_coords = self.requestion.address.coords
        if sadik_coords and child_coords:
            return sadik_coords.distance(child_coords)
        else:
#            print('Dont know distance between %s and %s' %
#                (self.sadik_group.sadik.address, self.requestion.address))
            return 1


class TableArray(object):
    u"""
    Абстрактный класс для строки или столбца в таблице

    Параметр ``data`` в конструкторе должен быть противоложным,
    т.е. если создается строка, то data должна содержать 
    последовательность столбцов
    """

    def __init__(self, instance, qs):
        self.instance = instance   # объект, привязанный к массиву (садик или заявка)
        self.data = qs
        self.cells = set()

    def next(self):
        # Сохраняется сортировка как в QuerySet
        for item in self.data:
            yield self.get_cell(item)

    def __iter__(self):
        return self.next()

    def __getitem__(self, index):
        return self.get_cell(self.data[index])

    def add_cell(self, cell):
        self.cells.add(cell)

    def get_cell(self, instance):
        raise NotImplementedError


class Row(TableArray):

    def get_cell(self, instance):
        array = filter(lambda c: c.sadik_group == instance, self.cells)
        if array:
            return array[0]
        else:
            return None

    def __repr__(self):
        return '<Row for requestion %s>' % self.instance

    def weigh(self):
        u"""Взвесить заявки"""
        requestion = self.instance

        if requestion.distribute_in_any_sadik:
            # Распределяем вес между всеми доступными садиками
            if requestion.areas.all().exists():
                available_sadik_ids = requestion.areas.all(
                    ).values_list('sadik__id', flat=True)
                available_groups = SadikGroup.objects.filter(sadik__id__in=available_sadik_ids)
            else:
                available_groups = self.data
            preffered_sadiks = requestion.pref_sadiks.all()

            # Распределяем 60% веса между приоритетными
            # и всё остальное - между остальными

            preffered_total = 0
            other_total = 0

            for cell in self.cells:
                if cell.sadik_group.sadik in preffered_sadiks:
                    preffered_total += 1
                elif cell.sadik_group in available_groups:
                    other_total += 1

            # коэффициент взвешивания для приритетных садиков
            preffered_weight_factor = (CELL_WEIGHT * 0.6 / preffered_total
                if preffered_total else 0)

            # коэффициент взвешивания для остальных садиков
            if preffered_weight_factor:
                other_weight_factor = (CELL_WEIGHT * 0.4 / other_total
                    if other_total else 0)
            else:
                # Если приоритетных садиков нет, весь вес распределяется на доступные
                other_weight_factor = (CELL_WEIGHT / other_total
                    if other_total else 0)

            for cell in self.cells:
                if cell.sadik_group.sadik in preffered_sadiks:
                    cell.weight = preffered_weight_factor
                elif cell.sadik_group in available_groups:
                    cell.weight = other_weight_factor

        else:
            # Распределение ТОЛЬКО между приоритетными садиками
            preffered_sadiks = requestion.pref_sadiks.all()
            preffered_total = len([c for c in self
                if c.sadik_group.sadik in preffered_sadiks])
#            может упасть, если не указаны приоритетные ДОУ(заявка не может быть никуда зачислена),
#            но такого не должно быть
            preffered_weight_factor = CELL_WEIGHT / preffered_total

            for cell in self.cells:
                if cell.sadik_group.sadik in preffered_sadiks:
                    cell.weight = preffered_weight_factor

        self.total_weight = sum([c.weight for c in self])

    @property
    def available_groups_count(self):
        u"""Количество групп, в которые можно зачислить"""
        return len([c for c in self.cells if c.weight > 0])


class Col(TableArray):

    def get_cell(self, instance):
        array = filter(lambda c: c.requestion == instance, self.cells)
        if array:
            return array[0]
        else:
            return None

    def set_popularity(self):
        u"""Установить популярность"""
        if self.instance.free_places:
            self.popularity = sum([cell.weight for cell in self.cells]) / self.instance.free_places
        else:
            self.popularity = 0

    def __repr__(self):
        return '<Column for sadik group %s>' % self.instance


class Arrays(list):
    u"""Абстракция над набором столбцов/строк таблицы"""
    TableArrayClass = None

    def __init__(self, qs, cell_qs, *args, **kwds):
        u"""
        Надстройка над типом set, индексация сделана по нумерации QuerySet,
        передаваемого в конструктор.

        Параметр ``cell_qs`` нужен для индексации внутри создаваемых массивов,
        должен быть противоложным Queryset-ом
        """
        self.qs = qs
        self.cell_qs = cell_qs
        super(Arrays, self).__init__(*args, **kwds)

    def __getitem__(self, index):
        return self.get_table_array(self.qs[index])

    def get_table_array(self, instance):
        u"""
        Возвращает объект подкласса ``TableArray`` по нужному объекту из списка ``iterable``
        """
        array = filter(lambda x: x.instance.pk == instance.pk, self)
        if array:
            return array[0]
        else:
            return None

    def get_or_create_table_array(self, instance):
        if self.get_table_array(instance):
            return self.get_table_array(instance)
        else:
            arr = self.TableArrayClass(instance, qs=self.cell_qs)
            self.append(arr)
            return arr


class Cols(Arrays):

    TableArrayClass = Col

    def get_col(self, *args):
        return self.get_table_array(*args)

    def get_or_create_col(self, *args):
        return self.get_or_create_table_array(*args)

    def weigh_popularity(self):
        total_popularity = sum([c.popularity for c in self])
        if total_popularity:
            popularity_factor = POPULARITY_weight / total_popularity
            for col in self:
                col.popularity *= popularity_factor



class Rows(Arrays):

    TableArrayClass = Row

    def get_row(self, *args):
        return self.get_table_array(*args)

    def get_or_create_row(self, *args):
        return self.get_or_create_table_array(*args)


class RowGroup(list):
    u"""
    Группа заявок с одинаковым количеством доступных к зачислению садиков
    """

    def __init__(self, num, iterable):
        super(RowGroup, self).__init__(iterable)
        self.num = num


class DataTable(object):
    u"""
    Класс для таблицы распределения садиков между заявками
    """

    def __init__(self, group_qs, requestion_qs):
        object.__init__(self)
        self.group_qs = group_qs
        self.requestion_qs = requestion_qs

        self.cols = Cols(group_qs, requestion_qs)
        self.rows = Rows(requestion_qs, group_qs)
        self.cells = dict()

        for sadik_group, requestion in product(group_qs, requestion_qs):
            self.add_cell(sadik_group, requestion)

        # Взвесить все строки
        map(lambda r: r.weigh(), self.rows)
        # Взвесить все столбцы
        map(lambda c: c.set_popularity(), self.cols)
        self.cols.weigh_popularity()
        # Создать группы
        self.create_row_groups()


    def add_cell(self, sadik_group, requestion):
        cell = Cell(sadik_group, requestion)
        self.cells['%s-%s' % (sadik_group.id, requestion.id)] = cell
        row = self.rows.get_or_create_row(requestion)
        row.add_cell(cell)
        col = self.cols.get_or_create_col(sadik_group)
        col.add_cell(cell)

    def create_row_groups(self):
        self.row_groups = []
        for key, group in groupby(self.rows, lambda r: r.available_groups_count):
            temp_group =list(group)
            row_group = RowGroup(key, [])

            for row in self.rows:
                if row in temp_group:
                    row_group.append(row)

            if row_group:
                self.row_groups.append(row_group)

        self.row_groups = sorted(self.row_groups, key=lambda g: g.num)

    def __getitem__(self, index):
        u"""Индексация сначала по строкам, потом по столбцам"""
        return self.rows[index]

# -----------------------------------------------------------------------
# |                 печать  таблиц                                      |
# -----------------------------------------------------------------------

class PrintableColumn(list):

    def __init__(self, name, data, align='-'):
        list.__init__(self, data)
        self.name = name
        width = max([len(str(x)) for x in data])
        width= max(width, len(name))
        self.format = ' %%%s%ds ' % (align, width)


class PrintableTable(DataTable):

    def __init__(self, *args, **kwds):
        super(PrintableTable, self).__init__(*args, **kwds)
        self._print_columns = [
            PrintableColumn(name=unicode(col.instance).encode('utf8'), data=col)
            for col in self.cols
        ]
        self._print_length = max(len(x) for x in self._print_columns)

    def _get_print_row(self, i=None):
        for x in self._print_columns:
            if i is None:
                yield x.format % x.name
            else:
                yield x.format % x[i]

    def _get_print_rows(self):
        yield '|'.join(self._get_print_row(None))
        for i in range(0, self._print_length):
            yield '|'.join(self._get_print_row(i))

    def __str__(self):
        return '\n'.join(self._get_print_rows())
