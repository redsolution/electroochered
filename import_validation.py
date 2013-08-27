# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulStoneSoup
import json
import urllib
import urllib2
import sys
import os
import tempfile
import cPickle
import xlrd
from optparse import OptionParser
from xlrd.xldate import XLDateError
from xlutils.copy import copy
import datetime
import re
import xlwt

parser = OptionParser(usage=u"Использование: %prog [параметры] файл")
parser.add_option("--requestion-import", dest="requestion_import",
                  action="store_true", default=False,
                  help=u"импорт заявок")
parser.add_option("--sadik-import", dest="sadik_import",
                  action="store_true", default=False,
                  help=u"импорт ДОУ")
parser.add_option("--system-params-url", dest="system_params_url",
                  help=u"url для получения параметров системы")
(options, args) = parser.parse_args()

if not args:
    parser.error(u'Необходимо указать имя файла.')
if options.requestion_import and options.sadik_import:
    parser.error(u"Параметры --requestion-import и --sadik-import взаимоисключающие.")
if not options.requestion_import and not options.sadik_import:
    parser.error(u"Необходимо указать один из параметров: --requestion-import или --sadik-import")
if not options.system_params_url:
    parser.error(u'Необходимо указать параметр --system-params-url')


class SystemParams(dict):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SystemParams, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def get_from_url(self, url):
        try:
            response = urllib.urlopen(url)
            self.update(json.loads(response.readlines()[0]))
        except Exception:
            print u"Невозможно получить параметры системы, проверьте правильность url"
            sys.exit()

system_params = SystemParams()
system_params.get_from_url(options.system_params_url)

min_birth_date = lambda: datetime.date.today().replace(
    year=datetime.date.today().year - system_params["MAX_CHILD_AGE"])


class ErrorRow(list):

    def __init__(self, data, index, logic_exception=None):
        self.row_index = index
        self.logic_exception = logic_exception
        super(ErrorRow, self).__init__(data)


class ValidationError(Exception):

    def __init__(self, message):
        if isinstance(message, list):
            self.messages = [msg for msg in message]
        else:
            self.messages = [message,]


# геокодер яндекса
class Geocoder(object):
    base_url = ''
    defaults = None

    def __init__(self, **kwargs):
        if self.defaults:
            self.params = self.defaults
        else:
            self.params = {}

        self.params.update(**kwargs)
        self.params['encoded_params'] = self.encode_params(self.params.copy())
        object.__init__(self)

    def encode_params(self, kwargs):
        if 'encoded_params' in kwargs:
            kwargs.pop('encoded_params')
        if 'query' in kwargs:
            kwargs.pop('query')
        return urllib.urlencode(kwargs)

    def geocode(self, query):
        attempts = 0
        while attempts < 3:
            try:
                self.params['query'] = urllib.quote_plus(query.encode('utf-8'))

                url = self.base_url % self.params

                data = urllib2.urlopen(url)
                response = data.read()

                return self.parse_response(response)
            except Exception:
                attempts += 1

    def parse_response(self, data):
        return data


class Yandex(Geocoder):
    u"""
    Реализация Яндекс - геокодера
    http://api.yandex.ru/maps/doc/geocoder/desc/concepts/input_params.xml

    В конструктор класса передаются параметры,
    в функцию geocode - строка запроса.

    ``geocode`` возвращает кортеж из координат, либо None

    Аргумент ``bounds`` используется для ограничения области поиска.
    Формат аргмуента: кортеж из четырёх значений коодинат, например, (lat1, lng1, lat2, lng2)
    """
    base_url = 'http://geocode-maps.yandex.ru/1.x/?geocode=%(query)s&%(encoded_params)s'
    defaults = {
        'format': 'xml',
    }

    def encode_params(self, kwargs):
        if 'bounds' in kwargs:
            x1, y1, x2, y2 = kwargs.pop('bounds')
            ll = ((x1+x2)/2, (y1+y2)/2)  # координаты центра области
            spn = (abs(ll[0] - x1), abs(ll[1] - y1))  # протяженность области в градусах

            kwargs['ll'] = '%f,%f' % ll
            kwargs['spn'] = '%f,%f' % spn

        return super(Yandex, self).encode_params(kwargs)

    def parse_response(self, data):
        soup = BeautifulStoneSoup(data)
        found = soup.ymaps.geoobjectcollection.metadataproperty.geocoderresponsemetadata.found.string
        if found != '0':
            return tuple(soup.ymaps.geoobjectcollection.featuremember.geoobject.point.pos.string.split(' '))

# парсеры ячеек

XL_CELL_EMPTY = 0   # empty string u''
XL_CELL_TEXT = 1    # a Unicode string
XL_CELL_NUMBER = 2  # float
XL_CELL_DATE = 3    # float
XL_CELL_BOOLEAN = 4 # int; 1 means TRUE, 0 means FALSE
XL_CELL_ERROR = 5   # int representing internal Excel codes; for a text representation, refer to the supplied dictionary error_text_from_code
XL_CELL_BLANK = 6   # empty string u''. Note: this type will appear only when open_workbook(..., formatting_info=True) is used.

class CellParserMismatch(Exception):

    def __init__(self):
        self.messages = [u'Неверный тип поля', ]

class CellParser(object):
    parser_type = None

    def __init__(self, value, datemode):
        self.value = value
        self.datemode = datemode

    def to_python(self):
        """return python object or raise ValueError"""
        raise NotImplementedError('Override this method in children class')
        raise NotImplementedError('Override this method in children class')


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


class SadikNumberCellParser(TextNumberCellParser):

    def to_python(self):
        return [super(SadikNumberCellParser, self).to_python()]


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
                             system_params["AGENT_TYPE_CHOICES"]])
        if text in choices_dict:
            return choices_dict[text]
        else:
            raise ValidationError(u'Неверный тип представительства')


class BenefitsCellParser(CellParser):
    u"""Получаем льготы по названию"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        text = self.value
        text = re.sub("\n", ' ', text)
        text = re.sub("\s\s+", ' ', text)
        text = text.strip()
#        разбиваем по именам льгот
        benefits_names = text.split(';')
        benefits = []
        wrong_benefit_names = []
        for benefit_name in benefits_names:
            benefit_name = benefit_name.strip()
#            проверяем есть ли льгота с таким названием и возвращаем, если есть
            if benefit_name in system_params["BENEFITS"]:
                benefits.append(benefit_name)
            else:
                wrong_benefit_names.append(benefit_name)
        if wrong_benefit_names:
            raise ValidationError(
                u'Льготы со следующими именами не зарегистрированы в системе: %s' %
                    u';'.join([name for name in wrong_benefit_names]))
        else:
            return benefits


class DesiredDateMixin(object):
    def to_python(self):
        year = super(DesiredDateMixin, self).to_python()
        if year > (datetime.date.today().year + system_params["MAX_CHILD_AGE"]):
            raise ValidationError(u"Слишком большой желаемый год зачисления")
        if year:
            return datetime.date(year, 01, 01)


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
        text = re.sub("\n", ' ', text)
        text = re.sub("\s\s+", ' ', text)
        text = text.strip()
        if text:
            if text in system_params["AREAS"]:
                return text
            else:
                raise ValidationError(
                    u"В базе нет территориальной области с названием %s" % text)
        else:
            raise ValidationError(u"Неверный тип поля")


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


class DocumentParserMixin(object):
    u"""Возвращает словарь, содержащий документ и шаблон документа, подходящий для данного номера"""

    def to_python(self):
        document_number = super(DocumentParserMixin, self).to_python()
        if document_number:
            for document_template in system_params["REQUESTION_DOCUMENTS_TEMPLATES"]:
                if re.match(document_template['regex'], document_number):
                    return {'document_number': document_number,
                            'template_name': document_template['name']}
        raise ValidationError(u'Номер документа %s не подходит ни под один шаблон' % document_number)


class DocumentTextCellParser(DocumentParserMixin, TextCellParser):
    u"""получение документа, хранимого в виде текста"""


class DocumentNumberCellParser(DocumentParserMixin, TextNumberCellParser):
    u"""получение документа, хранимого в виде числа"""


class AgeGroupCellParser(CellParser):
    u"""Получаем льготы"""
    parser_type = XL_CELL_TEXT

    def to_python(self):
        text = self.value
        text = re.sub("\n", ' ', text)
        text = re.sub("\s\s+", ' ', text)
        text = text.strip()
#        разбиваем по именам льгот
        age_groups_identifiers = [identifier.strip() for identifier in text.split(';') if identifier.strip()]
        wrong_age_groups_identifiers = []
        for age_group_identifier in age_groups_identifiers:
            if age_group_identifier:
    #            проверяем есть ли льгота с таким названием и возвращаем, если есть
                if age_group_identifier not in system_params["AGE_GROUPS"]:
                    wrong_age_groups_identifiers.append(u'"%s"' % age_group_identifier)
        if wrong_age_groups_identifiers:
            raise ValidationError(
                u'Следующие возрастные группы не зарегистрированы в системе: %s' %
                u'; '.join(wrong_age_groups_identifiers))
        else:
            return age_groups_identifiers


dummy_parsers = (DummyBlankCell, DummyDateCell, DummyEmptyCell, DummyTextCell,
                DummyNumberCell)
blank_parsers = (BlankCellParser, EmptyToBlankCellParser)
blank_empty_parsers = (EmptyCellParser, BlankCellParser)
none_parsers = (EmptyCellParser, BlankToEmptyCellParser)


def get_xlwt_style_list(rdbook):
    u"""
    утилита для копирования стилей xls
    """
    wt_style_list = []
    for rdxf in rdbook.xf_list:
        wtxf = xlwt.Style.XFStyle()
        #
        # number format
        #
        wtxf.num_format_str = rdbook.format_map[rdxf.format_key].format_str
        #
        # font
        #
        wtf = wtxf.font
        rdf = rdbook.font_list[rdxf.font_index]
        wtf.height = rdf.height
        wtf.italic = rdf.italic
        wtf.struck_out = rdf.struck_out
        wtf.outline = rdf.outline
        wtf.shadow = rdf.outline
        wtf.colour_index = rdf.colour_index
        wtf.bold = rdf.bold #### This attribute is redundant, should be driven by weight
        wtf._weight = rdf.weight #### Why "private"?
        wtf.escapement = rdf.escapement
        wtf.underline = rdf.underline_type ####
        # wtf.???? = rdf.underline #### redundant attribute, set on the fly when writing
        wtf.family = rdf.family
        wtf.charset = rdf.character_set
        wtf.name = rdf.name
        #
        # protection
        #
        wtp = wtxf.protection
        rdp = rdxf.protection
        wtp.cell_locked = rdp.cell_locked
        wtp.formula_hidden = rdp.formula_hidden
        #
        # border(s) (rename ????)
        #
        wtb = wtxf.borders
        rdb = rdxf.border
        wtb.left = rdb.left_line_style
        wtb.right = rdb.right_line_style
        wtb.top = rdb.top_line_style
        wtb.bottom = rdb.bottom_line_style
        wtb.diag = rdb.diag_line_style
        wtb.left_colour = rdb.left_colour_index
        wtb.right_colour = rdb.right_colour_index
        wtb.top_colour = rdb.top_colour_index
        wtb.bottom_colour = rdb.bottom_colour_index
        wtb.diag_colour = rdb.diag_colour_index
        wtb.need_diag1 = rdb.diag_down
        wtb.need_diag2 = rdb.diag_up
        #
        # background / pattern (rename???)
        #
        wtpat = wtxf.pattern
        rdbg = rdxf.background
        wtpat.pattern = rdbg.fill_pattern
        wtpat.pattern_fore_colour = rdbg.pattern_colour_index
        wtpat.pattern_back_colour = rdbg.background_colour_index
        #
        # alignment
        #
        wta = wtxf.alignment
        rda = rdxf.alignment
        wta.horz = rda.hor_align
        wta.vert = rda.vert_align
        wta.dire = rda.text_direction
        # wta.orie # orientation doesn't occur in BIFF8! Superceded by rotation ("rota").
        wta.rota = rda.rotation
        wta.wrap = rda.text_wrapped
        wta.shri = rda.shrink_to_fit
        wta.inde = rda.indent_level
        # wta.merg = ????
        #
        wt_style_list.append(wtxf)
    return wt_style_list


# форматы для списка заявок и ДОУ
class Format(object):

    cells = []  # override this

    # xls reading options
    start_line = 0
    sheet_num = 0

    def __init__(self, document, name=None):
        """
        name - internal format name
        cell_parser - iterable object, contains row cells for validation
        for example:
            [(cell1,),
             (cell2,),
             (cell3_1, cell3_2),
             (cell4,)]
        If validation in cell3_1 fails, format will try to validate cell3_2.
        """
        self.name = name
        self.document = document
        self.cell_data = []
        self.sheet = self.document.sheet_by_index(self.sheet_num)

    def to_python(self, data_row):
        """
        Returns python object with all required data
        Object should not expect any Exception subclasses in data_row
        Should return tuple of objects:
            requestion, profile, sadik_number_list
        """
        raise NotImplementedError('Override this method in children class')

    def _run_cell_parser(self, cell_parser, cell_data):
        """Validate cell data through parser"""
        if cell_parser.parser_type == cell_data.ctype:
            return cell_parser(cell_data.value, self.document.datemode).to_python()
        else:
            raise CellParserMismatch()

    def __iter__(self):
        return self.next()

    def next(self):
        # per-row validation
        for rownum in range(self.start_line, self.sheet.nrows):
            data_row = self.sheet.row_slice(rownum)[:len(self.cells)]
            parsed_data = []

            # per-cell validation
            for i, cell_data in enumerate(data_row):
                # temp variables
                exception = None
                value = None
                ok = False  # bool if any value returned
                # run all parsers
                for cell_parser in self.cells[i]['parsers']:
                    try:
                        value = self._run_cell_parser(cell_parser, cell_data)
                        ok = True
                        break
                    except ValidationError, e:
                        if exception is None:
                            exception = e
                        else:
                            pass  # go to next cellparser
                    except CellParserMismatch:
                        pass  # go to next cellparser

                # store value and exception data
                if (not ok) and (exception is None):
                    exception = CellParserMismatch()
                if ok:
                    parsed_data.append(value)
                else:
                    parsed_data.append(exception)

            yield parsed_data


cells = [
    {'name':u'Регистрационный № в очереди', 'parsers':(TextCellParser, TextDecimalNumberCellParser) + blank_empty_parsers}, # 0
    {'name':u'Территориальная область', 'parsers':(AreaCellParser,)}, # 1

#    дата регистрации
    {'name':u'День регистрации', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 2
    {'name':u'Месяц регистрации', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 3
    {'name':u'Год регистрации', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 4

    {'name':u'Свидетельство о рождении', 'parsers':(DocumentTextCellParser, DocumentNumberCellParser)+blank_empty_parsers}, # 5

    {'name':u'Фамилия ребёнка', 'parsers':(TextCellParser,)}, # 6
    {'name':u'Имя ребёнка', 'parsers':(TextCellParser,)}, # 7
    {'name':u'Отчество ребёнка', 'parsers':(TextCellParser,)}, # 8

#    дата рождения
    {'name':u'День рождения', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 9
    {'name':u'Месяц рождения', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 10
    {'name':u'Год рождения', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 11

    {'name':u'Пол', 'parsers':(SexCellParser,)}, # 12

    {'name':u'Домашний адрес: почтовый индекс',
        'parsers': (PostIndexIntegerCellParser, PostIndexTextCellParser)}, # 13
    {'name':u'Домашний адрес: Населенный пункт',
     'parsers': (TextCellParser,)}, # 14
    {'name':u'Домашний адрес: номер квартала', 'parsers':
        (TextCellParser, TextNumberCellParser) + blank_empty_parsers}, # 15
    {'name':u'Домашний адрес: улица', 'parsers':
        (TextCellParser,)}, # 16
    {'name':u'Домашний адрес: дом', 'parsers':
        (TextCellParser, TextDecimalNumberCellParser) + blank_empty_parsers}, # 17
    {'name':u'Домашний адрес: квартира', 'parsers':
        (TextCellParser, TextDecimalNumberCellParser) + blank_empty_parsers}, # 18

    {'name':u'Основной телефон', 'parsers':
        (TextCellParser, TextDecimalNumberCellParser,) + blank_empty_parsers}, # 19
    {'name':u'Дополнительный телефон', 'parsers':
        (TextCellParser, TextDecimalNumberCellParser,) + blank_empty_parsers}, # 20

#    родитель
    {'name':u'Фамилия родителя', 'parsers':
        (TextCellParser,) + blank_empty_parsers}, # 21
    {'name':u'Имя родителя', 'parsers':
        (TextCellParser,) + blank_empty_parsers}, # 22
    {'name':u'Отчество родителя', 'parsers':
        (TextCellParser,) + blank_empty_parsers}, # 23

    {'name':u'Вид представительства', 'parsers':
        (AgentTypeCellParser,)}, # 24
    {'name': u'Льготы', 'parsers': (BenefitsCellParser,) + blank_empty_parsers}, # 25
    {'name':u'Желаемый ДОУ', 'parsers':
        (SadikNumberCellParser, MultiSadikNumberCellParser,)
            + blank_empty_parsers}, # 26
    {'name':u'Год начала зачисления', 'parsers':
        (DesiredDateCellNumberParser, DesiredDateCellTextParser)
            + blank_empty_parsers}, # 27
]


class RequestionFormat(Format):

    # xls reading options
    start_line = 2
    document_cell_index = 5
    cells = cells

    @staticmethod
    def get_address_text(address_data):
        address_elements = []
        if address_data["town"]:
            town = "%s," % address_data["town"]
            address_elements.append(town)
        if address_data["building_number"] and address_data["street"]:
            street = "%s," % address_data["street"]
        else:
            street = address_data["street"]
        address_elements.extend([address_data["block_number"], street, address_data["building_number"]])
        return u" ".join([el for el in address_elements if el])

    def to_python(self, data_row_with_errors):
        # Задать год зачисления текущим, если он не указан
        data_row = []
        errors = []
        for cell in data_row_with_errors:
            if isinstance(cell, Exception):
                data_row.append(None)
            else:
                data_row.append(cell)
        if all((data_row[4], data_row[3], data_row[2])):
            try:
                registration_date = datetime.date(data_row[4], data_row[3], data_row[2])
            except ValueError, e:
                errors.append(u'Неверная дата регистрации: %s' % e)
                registration_date = None
        else:
            registration_date = None
        if all((data_row[11], data_row[10], data_row[9])):
            try:
                birth_date = datetime.date(data_row[11], data_row[10], data_row[9])
            except ValueError, e:
                errors.append(u'Неверная дата рождения: %s' % e)
                birth_date = None
        else:
            birth_date = None
        requestion_data = {
            'number_in_old_list': data_row[0],
            'registration_datetime': registration_date,
            'birth_date': birth_date,
            'sex': data_row[12],
            'admission_date': data_row[27],
            'name': data_row[7],
        }
        requestion_data.update({
            'distribute_in_any_sadik': True,
            })
        area = data_row[1]
        if area:
            areas = (area,)
        else:
            areas = ()
        if data_row[26]:
            if type(data_row[26]) is int:
                preferred = [data_row[26]]
            else:
                preferred = data_row[26]
        else:
            preferred = []
        address_data = {
            'town': data_row[14],
            'postindex': data_row[13],
            'block_number': data_row[15],
            'street': data_row[16],
            'building_number': data_row[17],
            }
        requestion_data['location_properties'] = self.get_address_text(address_data)
        benefits = data_row[25]
        document = data_row[5]
        return requestion_data, areas, preferred, benefits, document, errors


sadik_list_cells = (
    {'name':u'Территориальная область', 'parsers':(AreaCellParser,)}, # 0
    {'name':u'Полное название', 'parsers': (TextCellParser,)}, # 1
    {'name':u'Короткое название', 'parsers': (TextCellParser,)}, # 2
    {'name':u'Идентификатор', 'parsers': (TextNumberCellParser, TextCellParser)}, # 3

#    директор
    {'name':u'Фамилия директора', 'parsers':
        (TextCellParser,) + blank_empty_parsers}, # 4
    {'name':u'Имя директора', 'parsers':
        (TextCellParser,) + blank_empty_parsers}, # 5
    {'name':u'Отчество директора', 'parsers':
        (TextCellParser,) + blank_empty_parsers}, # 6

#    адрес
    {'name':u'Адрес: населенный пункт', 'parsers':
        (TextCellParser,)+blank_empty_parsers}, # 7
    {'name':u'Адрес: почтовый индекс', 'parsers':
        (PostIndexIntegerCellParser, PostIndexTextCellParser)}, # 8
    {'name':u'Адрес: номер квартала', 'parsers':
        (TextCellParser, TextNumberCellParser)+blank_empty_parsers}, # 9
    {'name':u'Адрес: улица', 'parsers':
        (TextCellParser,)+blank_empty_parsers}, # 10
    {'name':u'Адрес: дом', 'parsers':
        (TextCellParser, TextDecimalNumberCellParser) + blank_empty_parsers}, # 11

#дополнительная информация
    {'name':u'Телефон', 'parsers':
        (TextCellParser, TextDecimalNumberCellParser,) + blank_empty_parsers}, # 12
    {'name':u'Адрес сайта', 'parsers':
        (TextCellParser, ) + blank_empty_parsers}, # 13
    {'name':u'Адрес электронной почты', 'parsers':
        (TextCellParser, ) + blank_parsers}, # 14
    {'name':u'Техническая оснащенность', 'parsers':
        (TextCellParser, ) + blank_empty_parsers}, # 15
    {'name':u'Учебные программы дополнительного образования', 'parsers':
        (TextCellParser, ) + blank_empty_parsers}, # 16
    {'name':u'Дополнительная информация', 'parsers':
        (TextCellParser, ) + blank_empty_parsers}, # 17
    {'name':u'Возрастные группы', 'parsers': (AgeGroupCellParser,) + blank_empty_parsers}, # 18

    {'name':u'Широта', 'parsers': (DecimalNumberCellParser, DecimalTextCellParser)}, # 19
    {'name':u'Долгота', 'parsers': (DecimalNumberCellParser, DecimalTextCellParser)}, # 20
)

class SadikFormat(Format):

    # xls reading options
    start_line = 2
    cells = sadik_list_cells
    def to_python(self, data_row_with_errors):
        data_row = []
        for cell in data_row_with_errors:
            if isinstance(cell, Exception):
                data_row.append(None)
            else:
                data_row.append(cell)
        last_name = data_row[4]
        first_name = data_row[5]
        patronymic = data_row[6]
        full_name = ' '.join([el for el in (last_name, first_name, patronymic) if el])
        sadik_data = {
            "name": data_row[1],
            "short_name": data_row[2],
            "identifier": data_row[3],
            "head_name": full_name,
            "phone": data_row[12],
            "site": data_row[13],
            "email": data_row[14],
            "tech_level": data_row[15],
            "training_program": data_row[16],
            "extended_info": data_row[17],
        }
        if data_row[0]:
            sadik_data.update({"area": data_row[0]})
        latitude = data_row[19]
        longtitude = data_row[20]
        address_data = {
            'town': data_row[7],
            'postindex': data_row[8],
            'block_number': data_row[9],
            'street': data_row[10],
            'building_number': data_row[11],
            }
        if longtitude and latitude:
            coords = {'latitude': latitude, 'longtitude': longtitude}
        else:
            coords = {}
        age_groups = data_row[18]
        return sadik_data, address_data, coords, age_groups


# логика обработки заявок и ДОУ
class RequestionLogic(object):

    def __init__(self, format_doc):
        """
        Describes main buisness logic in import process
        format_doc - instance of subclass of Format
        """
        self.format_doc = format_doc
        self.errors = []
        self.new_identificators = []
        self.requestion_documents = []
        self.import_data = []

    def validate(self):
        """
        Run through cells, if cell is valid, store python value,
        if not - store error information
        """
        for index, parsed_row in enumerate(self.format_doc):
            cell_errors = any([issubclass(type(cell), Exception) for cell in parsed_row])
            try:
                self.validate_record(self.format_doc.to_python(parsed_row), cell_errors, index)
            except ValidationError, e:
                logic_errors = e
            else:
                logic_errors = None
            if cell_errors or logic_errors:
                self.errors.append(ErrorRow(parsed_row, index + self.format_doc.start_line, logic_errors))

    def validate_record(self, data_tuple, cell_errors, row_index):
        requestion_data, areas, sadiks_identifiers_list, benefits, document, errors = data_tuple
#        если у заявки не указано время регистрации, то устанавливаем 9:00
        if type(requestion_data.get('registration_datetime')) is datetime.date:
            requestion_data['registration_datetime'] = datetime.datetime.combine(
                requestion_data['registration_datetime'], datetime.time(9, 0))
        if document:
            try:
                self.validate_document_duplicate(document)
            except ValidationError, e:
                errors.extend(e.messages)
        registration_datetime = requestion_data.get("registration_datetime")
        if registration_datetime:
            try:
                self.validate_registration_date(registration_datetime)
            except ValidationError, e:
                errors.extend(e.messages)
        birth_date = requestion_data.get("birth_date")
        if registration_datetime and birth_date:
            try:
                self.validate_dates(registration_datetime, birth_date)
            except ValidationError, e:
                errors.extend(e.messages)
        if sadiks_identifiers_list:
            try:
                preferred_sadiks = self.validate_sadik_list(sadiks_identifiers_list)
            except ValidationError, e:
                errors.extend(e.messages)
        else:
            preferred_sadiks = []
        try:
            self.validate_admission_date(requestion_data)
        except ValidationError, e:
            errors.extend(e.messages)
        #self.validate_field_length(requestion_data, document_number)
        if errors:
            raise ValidationError(errors)
        else:
            if not cell_errors:
                if not document:
                    document_number = "TMP_%07d" % row_index
                    self.new_identificators.append({'row_index': row_index + self.format_doc.start_line,
                                                    'document_number': document_number})
                    if system_params["REQUESTION_DOCUMENTS_TEMPLATES"]:
                        template_name = system_params["REQUESTION_DOCUMENTS_TEMPLATES"][0]["name"]
                    else:
                        template_name = ''
                    document = {
                        "document_number": document_number,
                        "fake": True,
                        "template_name": template_name,
                    }
                else:
                    document.update({'fake': False})
                self.import_data.append({
                    'requestion_data': requestion_data,
                    'areas': areas,
                    'sadiks_identifiers_list': sadiks_identifiers_list,
                    'benefits_names': benefits,
                    'document': document
                })

    def validate_document_duplicate(self, document):
        if document["document_number"] in self.requestion_documents:
            raise ValidationError(u'Заявка с документом "%s" уже встречается в файле' % document["document_number"])
        else:
            self.requestion_documents.append(document["document_number"])



    @staticmethod
    def validate_registration_date(registration_datetime):
        u"""заявки должны быть поданы до теукщей даты"""
        if datetime.date.today() < registration_datetime.date():
            raise ValidationError(
                u'Дата регистрации не может быть больше текущей даты.')
        elif datetime.date.today() == registration_datetime.date():
            raise ValidationError(
                u'Дата регистрации не может совпадать с текущей датой.')

    @staticmethod
    def validate_dates(registration_datetime, birth_date):
        u"""проверка, что дата рождения попадает в диапазон для зачисления и
        дата регистрации больше даты рождения"""

        if datetime.date.today() < birth_date or birth_date <= min_birth_date():
            raise ValidationError(u'Возраст ребёнка не подходит для зачисления в ДОУ.')
        if registration_datetime.date() < birth_date:
            raise ValidationError(u'Дата регистрации меньше даты рождения ребёнка.')

    @staticmethod
    def validate_sadik_list(sadik_number_list):
        u"""проверяем, номера ДОУ"""
        errors = []
        for sadik_number in sadik_number_list:
            if sadik_number not in system_params["SADIKS"]:
                errors.append(
                    u'В системе нет ДОУ с номером %s' % sadik_number)
        if errors:
            raise ValidationError(errors)
        else:
            return sadik_number_list

    @staticmethod
    def validate_admission_date(requestion_data):
        admission_date = requestion_data.get("admission_date")
        if admission_date and (admission_date.year >
                datetime.date.today().year + system_params["MAX_CHILD_AGE"]):
            raise ValidationError(u'Для желаемого года зачисления указано слишком большое значение.')

    def save_xls_results(self, path_to_file):
        u"""в UPLOAD_ROOT создаётся файл с именем file_name в котором строки с ошибками красные"""
        rb = self.format_doc.document
        rb_sheet = rb.sheet_by_index(0)
        wb = copy(rb)
        ws = wb.get_sheet(0)
        styles = get_xlwt_style_list(rb)
        for error in self.errors:
            row = rb_sheet.row(error.row_index)
            style = xlwt.easyxf('pattern: pattern solid, fore_colour red; align: horiz centre, vert centre; borders: top thin, bottom thin, left thin, right thin;')
            for i, cell in enumerate(row):
                style.num_format_str = styles[cell.xf_index].num_format_str
                ws.write(error.row_index, i, cell.value, style)
        for identificator in self.new_identificators:
            ws.write(identificator["row_index"],
                     self.format_doc.document_cell_index, identificator["document_number"])
        wb.save(path_to_file)


class SadikLogic(object):
    sadiks_identifiers = []
    errors = []
    import_data = []

    def __init__(self, format_doc):
        self.format_doc = format_doc

    def validate(self):
        for index, parsed_row in enumerate(self.format_doc):
            cell_errors = any([issubclass(type(cell), Exception) for cell in parsed_row])
            try:
                self.validate_record(self.format_doc.to_python(parsed_row), cell_errors=cell_errors)
            except ValidationError, e:
                logic_errors = e
            else:
                logic_errors = None
            if cell_errors or logic_errors:
                self.errors.append(ErrorRow(parsed_row, index + self.format_doc.start_line, logic_errors))

    def validate_record(self, data_tuple, cell_errors):
        sadik_data, address_data, coords, age_groups = data_tuple
        errors = []
        if sadik_data["identifier"]:
            try:
                self.validate_identifier(sadik_data)
            except ValidationError, e:
                errors.extend(e.messages)
        if errors:
            raise ValidationError(errors)
        else:
            if not cell_errors:
                self.import_data.append({
                    'sadik_data': sadik_data,
                    'address_data': address_data,
                    'coords': coords,
                    'age_groups': age_groups,
                })

    def validate_identifier(self, sadik_object):
        errors = []
        if sadik_object["identifier"] in self.sadiks_identifiers:
            errors.append(u'ДОУ с идентификатором "%s" уже встречается' % sadik_object["identifier"])
        else:
            self.sadiks_identifiers.append(sadik_object["identifier"])
        if sadik_object["identifier"] in system_params["SADIKS"]:
            errors.append(u'ДОУ с идентификатором "%s" уже есть в системе' % sadik_object["identifier"])
        if errors:
            raise ValidationError(errors)

    def save_xls_results(self, path_to_file):
        u"""в UPLOAD_ROOT создаётся файл с именем file_name в котором строки с ошибками красные"""
        rb = self.format_doc.document
        rb_sheet = rb.sheet_by_index(0)
        wb = copy(rb)
        ws = wb.get_sheet(0)
        styles = get_xlwt_style_list(rb)
        for error in self.errors:
            row = rb_sheet.row(error.row_index)
            style = xlwt.easyxf('pattern: pattern solid, fore_colour orange; align: horiz centre, vert centre; borders: top thin, bottom thin, left thin, right thin;')
            for i, cell in enumerate(row):
                style.num_format_str = styles[cell.xf_index].num_format_str
                ws.write(error.row_index, i, cell.value, style)
        wb.save(path_to_file)

def save_file_with_errors(errors_file_path, logic):
    file_with_errors = file(errors_file_path, "wb")
    for row in logic.errors:
        message = u"Ошибки в строке %d\n" % (row.row_index + 1)
        message = message.encode('utf-8')
        file_with_errors.write(message)
        if row.logic_exception:
            for message in row.logic_exception.messages:
                message_fix = u"%s\n" % message
                message_fix = message_fix.encode('utf-8')
                file_with_errors.write(message_fix)
        for i, cell in enumerate(row):
            if issubclass(type(cell), Exception):
                current_cell = logic.format_doc.cells[i]
                for error in cell.messages:
                    message = u"%s: %s\n" % (current_cell["name"], error)
                    file_with_errors.write(message.encode('utf-8'))
        file_with_errors.write("\n")
    file_with_errors.close()


def process(source_file_path, import_format):
    region_name = system_params["REGION_NAME"]
    geocoder = Yandex()

    def get_requestion_coords(location_properties):
        if region_name:
            address = "%s, %s" % (region_name, location_properties)
        else:
            address = location_properties
        coords = geocoder.geocode(address)
        if not coords:
            if region_name:
                coords = geocoder.geocode(region_name)
        return coords

    is_requestion_import = import_format == 'requestion_import'
    if is_requestion_import:
        print u"Проверка файла для импорта заявок"
        FormatClass = RequestionFormat
        LogicClass = RequestionLogic
    else:
        print u"Проверка файла для импорта ДОУ"
        FormatClass = SadikFormat
        LogicClass = SadikLogic
    source_file = open(source_file_path, 'r')
    descriptor, name = tempfile.mkstemp()
    os.fdopen(descriptor, 'wb').write(source_file.read())
    try:
        doc = xlrd.open_workbook(name, formatting_info=True)
    except xlrd.biffh.XLRDError:
        print u"Ошибка: Неверный тип файла. Для импорта необходимо использовать файлы формата xls"
    else:
        format_doc = FormatClass(doc)
        if format_doc.sheet.ncols >= len(format_doc.cells):
            logic = LogicClass(format_doc)
            logic.validate()
            dir_path, filename_full = os.path.split(source_file_path)
            filename, file_ext = os.path.splitext(filename_full)

            errors_file_path = os.path.join(dir_path, filename + '.txt')
            if logic.errors:
                save_file_with_errors(errors_file_path, logic)
                print u"В файле были найдены ошибки, вам необходимо исправить их. Файл со списком ошибок: %s" % errors_file_path
            else:
                # если все прошло нормально, то нужно сохранить данные в файл
                file_for_import_path = os.path.join(dir_path, filename + '.res')
                f = open(file_for_import_path, 'w')
                p = cPickle.Pickler(f)
                #сохраняем тип импорта(заявки или ДОУ)
                p.dump(import_format)
                if is_requestion_import:
                    print u"Проведена проверка. В файле ошибок не найдено. Выполняется операция определения координат и сохранение. Подождите. "
                    result_file_path = os.path.join(dir_path, filename + '_res' + file_ext)
                    logic.save_xls_results(result_file_path)
                    #определяем координаты и сохраняем данные по всем объектам
                    for instance_data in logic.import_data:
                        location_properties = instance_data["requestion_data"]["location_properties"]
                        instance_data["requestion_data"]["coords"] = get_requestion_coords(location_properties)
                        p.dump(instance_data)
                    print u"Операция выполнена успешно. Файл со сгенерированными идентификаторами номеров свидетельств: %s. Файл для импорта: %s" % (
                        result_file_path, file_for_import_path)
                else:
                    print u'Проведена проверка. В файле ошибок не найдено. Выполняется сохранение. Подождите. '
                    for instance_data in logic.import_data:
                        p.dump(instance_data)
                    print u"Операция выполнена успешно. Файл для импорта: %s" % file_for_import_path
                f.close()
        else:
            print u"Ошибка: Недостаточное количество столбцов"


if __name__=="__main__":
    if options.requestion_import:
        import_format = 'requestion_import'
    else:
        import_format = 'sadik_import'
    process(source_file_path=args[0].decode('utf-8'), import_format=import_format)