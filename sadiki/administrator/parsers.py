# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ValidationError
from sadiki.administrator.models import CellParser
from sadiki.conf_settings import DEFAULT_IMPORT_DOCUMENT_NAME
from sadiki.core.models import AGENT_TYPE_CHOICES, Benefit, BenefitCategory, \
    Area, AgeGroup, EvidienceDocumentTemplate, EvidienceDocument, REQUESTION_IDENTITY
from xlrd.xldate import XLDateError
import datetime
import re
import xlrd


XL_CELL_EMPTY = 0   # empty string u''
XL_CELL_TEXT = 1    # a Unicode string
XL_CELL_NUMBER = 2  # float
XL_CELL_DATE = 3    # float
XL_CELL_BOOLEAN = 4 # int; 1 means TRUE, 0 means FALSE
XL_CELL_ERROR = 5   # int representing internal Excel codes; for a text representation, refer to the supplied dictionary error_text_from_code
XL_CELL_BLANK = 6   # empty string u''. Note: this type will appear only when open_workbook(..., formatting_info=True) is used.


class DateCellParser(CellParser):
    u"""Дата"""
    parser_type = XL_CELL_DATE

    def to_python(self):
        try:
            date = xlrd.xldate_as_tuple(
                int(float(self.value)), int(self.datemode))
            date = datetime.date(date[0],
                date[1], date[2])
        except (ValueError, AttributeError, UnicodeError, XLDateError,
            IndexError):
            raise ValidationError(u'Неверная дата.')
        else:
            return date

class DateTextCellParser(CellParser):
    u"""Дата в текстовом формате"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        date_text = re.sub("\s", '', self.value)
        if re.match(ur'(?P<day>\d\d).(?P<month>\d\d).(?P<year>\d\d\d\d).?$', date_text):
            result = re.match(ur'(?P<day>\d\d).(?P<month>\d\d).(?P<year>\d\d\d\d).?$', date_text)
            day = int(result.group('day'))
            month = int(result.group('month'))
            year = int(result.group('year'))
        elif re.match(ur'(?P<day>\d\d).(?P<month>\d\d).(?P<year>\d\d).?$', date_text):
            result = re.match(ur'(?P<day>\d\d).(?P<month>\d\d).(?P<year>\d\d).?$', date_text)
            day = int(result.group('day'))
            month = int(result.group('month'))
            year = 2000 + int(result.group('year'))
        else:
            raise ValidationError(u'Неверная дата.')
        try:
            date = datetime.date(year, month, day)
        except ValueError:
            raise ValidationError(u'Неверная дата.')
        else:
            return date


class IntegerNumberCellParser(CellParser):
    u"""Номер в числовом формате"""
    parser_type = XL_CELL_NUMBER

    def to_python(self):
        if self.value - int(self.value):
            raise ValidationError(u'Поле не может быть вещественным числом с ненулевой дробной частью')
        else:
            return int(self.value)


class DecimalNumberCellParser(CellParser):
    u"""Вещественное число в числовом формате"""
    parser_type = XL_CELL_NUMBER

    def to_python(self):
        return self.value


class TextDecimalNumberCellParser(CellParser):
    u"""Номер с плавающей точкой в текстовом формате"""
    parser_type = XL_CELL_NUMBER

    def to_python(self):
        try:
            if self.value - int(self.value):
                return u'%s' % self.value
            else:
                return u'%d' % int(self.value)
        except (TypeError, ValueError):
            raise ValidationError(u'Поле не является числом')


class TextNumberCellParser(CellParser):
    u"""Преобразует число в текст"""
    parser_type = XL_CELL_NUMBER

    def to_python(self):
        try:
            return u'%d' % self.value
        except (TypeError, ValueError):
            raise ValidationError(u'Поле не является числом')

class MultiSadikNumberCellParser(CellParser):
    u"""Список номеров ДОУ, разделённых ;\s"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        sadiks = re.split(';', self.value)
        try:
            sadiks = [sadik.strip() for sadik in sadiks if sadik]
        except ValueError:
            raise ValidationError(u'Неверный формат списка ДОУ: %s' % self.value)
        else:
            return sadiks

class TextCellParser(CellParser):
    u"""Текст"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        text = self.value
        text = re.sub("\n", ' ', text)
        text = re.sub("\s\s+", ' ', text)
        text = text.strip()
        return text

class BirthCertNumberCellParser(CellParser):
    u"""Свидетельство о рождении"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        if any([re.match(regexp, self.value, re.UNICODE)
            for regexp in settings.BIRTH_CERT_REGEXP]):
            return self.value
        else:
            raise ValidationError(u'Номер свидетельства о рождении должен соответствовать формату. Указано %s' % self.value)

class EmptyCellParser(CellParser):
    parser_type = XL_CELL_EMPTY

    def to_python(self):
        return None

class EmptyToBlankCellParser(CellParser):
    parser_type = XL_CELL_EMPTY

    def to_python(self):
        return u''

class BlankCellParser(CellParser):
    parser_type = XL_CELL_BLANK

    def to_python(self):
        return u''

class BlankToEmptyCellParser(CellParser):
    u"""необходимо значение None"""
    parser_type = XL_CELL_BLANK

    def to_python(self):
        return None

class DummyBlankCell(CellParser):
    parser_type = XL_CELL_BLANK

    def to_python(self):
        pass


class DummyDateCell(CellParser):
    parser_type = XL_CELL_DATE

    def to_python(self):
        pass


class DummyEmptyCell(CellParser):
    parser_type = XL_CELL_EMPTY

    def to_python(self):
        pass


class DummyTextCell(CellParser):
    parser_type = XL_CELL_TEXT

    def to_python(self):
        pass


class DummyNumberCell(CellParser):
    parser_type = XL_CELL_NUMBER

    def to_python(self):
        pass


class SexCellParser(CellParser):
    parser_type = XL_CELL_TEXT

    def to_python(self):
        self.value = self.value.strip()
        if self.value in (u'м', u'М'):
            return u'М'
        elif self.value in (u'ж', u'Ж'):
            return u'Ж'
        else:
            raise ValidationError(u'Неверно укзан пол ("М", "Ж")')


class IntegerTextCellParser(CellParser):
    u"""Целое чилсло, хранимое в строковом формате"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        text = self.value.strip()
        try:
            number = int(text)
        except ValueError:
            raise ValidationError(u'Неверное целое число')
        else:
            return number


class DecimalTextCellParser(CellParser):
    u"""Вещественное число, хранимое в строковом формате"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        text = self.value
        text = re.sub("\n", '', text)
        text = re.sub("\s", '', text)
        try:
            number = float(text)
        except ValueError:
            raise ValidationError(u'Неверное вещественное число')
        else:
            return number


class AgentTypeCellParser(CellParser):
    u"""Вид представительства"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        text = self.value.strip()
#        получаем словарь с сопоставление наименования представительства и номера
        choices_dict = dict([(value, choice) for choice, value in
            AGENT_TYPE_CHOICES])
        if text in choices_dict:
            return choices_dict[text]
        else:
            raise ValidationError(u'Неверный тип представительства')


class BenefitsCellParser(CellParser):
    u"""Получаем льготы по названию"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        text = self.value.strip()
#        разбиваем по именам льгот
        benefits_names = [name.strip() for name in text.split(';')]
        benefits = []
        wrong_benefit_names = []
        for benefit_name in benefits_names:
            benefit_name = benefit_name.strip()
#            проверяем есть ли льгота с таким названием и возвращаем, если есть
            try:
                benefit = Benefit.objects.get(name=benefit_name)
                benefits.append(benefit)
            except Benefit.DoesNotExist:
                wrong_benefit_names.append(benefit_name)
        if wrong_benefit_names:
            raise ValidationError(
                u'Льготы со следующими именами не зарегистрированы в системе: %s' %
                    u';'.join([name for name in wrong_benefit_names]))
        else:
            return benefits


class BenefitCategoryCellMixin(object):
    def to_python(self):
        number = super(BenefitCategoryCellMixin, self).to_python()
        try:
            return BenefitCategory.objects.get(priority=number)
        except BenefitCategory.DoesNotExist:
            raise ValidationError(
                u"Категории с идентификатором %d не существует" % number)


class BenefitCategoryCellNumberParser(
        BenefitCategoryCellMixin, IntegerNumberCellParser):
    u"""получение категории льготы(когда хранение льгот недопускается)"""


class BenefitCategoryCellTextParser(
        BenefitCategoryCellMixin, IntegerTextCellParser):
    u"""получение категории льготы(когда хранение льгот недопускается)"""


class DesiredDateMixin(object):
    def to_python(self):
        year = super(DesiredDateMixin, self).to_python()
        if year > (datetime.date.today().year + settings.MAX_CHILD_AGE):
            raise ValidationError(u"Слишком большой желаемый год зачисления")
        if settings.DESIRED_DATE in (settings.DESIRED_DATE_SPEC_YEAR, settings.DESIRED_DATE_ANY):
            if year:
                return datetime.date(year, 01, 01)
        elif settings.DESIRED_DATE == settings.DESIRED_DATE_NEXT_YEAR:
            if year and year >= datetime.date.today().year:
                return datetime.date.today().replace(day=1, month=1)
        return None


class DesiredDateCellNumberParser(
        DesiredDateMixin, IntegerNumberCellParser):
    u"""получение ЖДП(в числовом формате)"""


class DesiredDateCellTextParser(
        DesiredDateMixin, IntegerTextCellParser):
    u"""получение ЖДП(в текстовом формате)"""
    
class AreaCellParser(CellParser):
    u"""Возвращает территориальную область по ее названию"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        text = self.value
        text = text.strip()
        if text:
            try:
                area = Area.objects.get(name=text)
            except Area.DoesNotExist:
                raise ValidationError(
                    u"В базе нет территориальной области с названием %s" % text)
            else:
                return area
        else:
            return u''


#TODO: возможно вместо парсеров индекса нужно воспользоваться валидацией модели
class PostIndexIntegerCellParser(IntegerNumberCellParser):

    def to_python(self):
        number = super(PostIndexIntegerCellParser, self).to_python()
        if number > 999999:
            raise ValidationError(u"Почтовый индекс должен соответствовать формату 999999")
        else:
            return number


class PostIndexTextCellParser(IntegerTextCellParser):

        def to_python(self):
            number = super(PostIndexTextCellParser, self).to_python()
            if number > 999999:
                raise ValidationError(u"Почтовый индекс должен соответствовать формату 999999")
            else:
                return number


class AgeGroupCellParser(CellParser):
    u"""Получаем льготы"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        text = self.value.strip()
        text = re.sub("\n", ' ', text)
        text = re.sub("\s\s+", ' ', text)
#        разбиваем по именам льгот
        age_groups_identifiers = text.split(';')
        age_groups = []
        wrong_age_groups_identifiers = []
        for age_group_identifier in age_groups_identifiers:
            if age_group_identifier.strip():
    #            проверяем есть ли льгота с таким названием и возвращаем, если есть
                try:
                    age_group = AgeGroup.objects.get(name=age_group_identifier.strip())
                    age_groups.append(age_group)
                except AgeGroup.DoesNotExist:
                    wrong_age_groups_identifiers.append(u'"%s"' % age_group_identifier.strip())
        if wrong_age_groups_identifiers:
            raise ValidationError(
                u'Следующие возрастные группы не зарегистрированы в системе: %s' %
                u'; '.join(wrong_age_groups_identifiers))
        else:
            return age_groups


class DocumentParserMixin(object):
    u"""Возвращает ноиер и тип документа, опирается на зачение DEFAULT_IMPORT_DOCUMENT_NAME в нсатройках, если документ
    не подходит под шаблон такого типа, то выбирается любой подходящий"""

    def to_python(self):
        document_number = super(DocumentParserMixin, self).to_python()
        if document_number:
            try:
                document_template = EvidienceDocumentTemplate.objects.get(name=DEFAULT_IMPORT_DOCUMENT_NAME)
            except EvidienceDocumentTemplate.DoesNotExist:
                document_template = None
            if document_template and re.match(document_template.regex, document_number):
                return EvidienceDocument(template=document_template, document_number=document_number,
                    confirmed=True)
            else:
                for document_template in EvidienceDocumentTemplate.objects.filter(destination=REQUESTION_IDENTITY):
                    if re.match(document_template.regex, document_number):
                        return EvidienceDocument(template=document_template, document_number=document_number,
                            confirmed=True)
        raise ValidationError(u'Номер документа %s не подходит ни под один шаблон' % document_number)


class DocumentTextCellParser(DocumentParserMixin, TextCellParser):
    u"""получение документа, хранимого в виде текста"""


class DocumentNumberCellParser(DocumentParserMixin, TextNumberCellParser):
    u"""получение документа, хранимого в виде числа"""



dummy_parsers = (DummyBlankCell, DummyDateCell, DummyEmptyCell, DummyTextCell,
                DummyNumberCell)
blank_parsers = (BlankCellParser, EmptyToBlankCellParser)
blank_empty_parsers = (EmptyCellParser, BlankCellParser)
none_parsers = (EmptyCellParser, BlankToEmptyCellParser)
