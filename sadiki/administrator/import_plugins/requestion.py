# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ValidationError
from sadiki.administrator.models import Format
from sadiki.administrator.parsers import TextCellParser, IntegerNumberCellParser, \
    MultiSadikNumberCellParser, TextDecimalNumberCellParser, SexCellParser, \
    blank_empty_parsers, AgentTypeCellParser, BenefitsCellParser, none_parsers, \
    BenefitCategoryCellNumberParser, BenefitCategoryCellTextParser, \
    DesiredDateCellNumberParser, DesiredDateCellTextParser, IntegerTextCellParser, \
    TextNumberCellParser, AreaCellParser, PostIndexIntegerCellParser, \
    PostIndexTextCellParser, DocumentNumberCellParser, DocumentTextCellParser
from sadiki.core.models import Requestion, Profile, STATUS_REQUESTER, \
    BenefitCategory
import datetime


cells = [
    {'name':u'Регистрационный № в очереди', 'parsers':(TextCellParser, TextDecimalNumberCellParser) + blank_empty_parsers}, # 0
    {'name':u'Территориальная область', 'parsers':(AreaCellParser,) + blank_empty_parsers}, # 1
    
#    дата регистрации
    {'name':u'День регистрации', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 2
    {'name':u'Месяц регистрации', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 3
    {'name':u'Год регистрации', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 4
    
    {'name':u'Свидетельство о рождении', 'parsers':(DocumentTextCellParser, DocumentNumberCellParser)+blank_empty_parsers}, # 5
    
    {'name':u'Фамилия ребёнка', 'parsers':(TextCellParser,) + blank_empty_parsers}, # 6
    {'name':u'Имя ребёнка', 'parsers':(TextCellParser,) + blank_empty_parsers}, # 7
    {'name':u'Отчество ребёнка', 'parsers':(TextCellParser,) + blank_empty_parsers}, # 8

#    дата рождения
    {'name':u'День рождения', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 9
    {'name':u'Месяц рождения', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 10
    {'name':u'Год рождения', 'parsers':(IntegerNumberCellParser, IntegerTextCellParser,)}, # 11

    {'name':u'Пол', 'parsers':(SexCellParser,) + blank_empty_parsers}, # 12

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
]
#в зависимости от типа хранения льгот задаем различные парсеры
if settings.FACILITY_STORE == settings.FACILITY_STORE_YES:
    cells += [{'name': u'Льготы', 'parsers': (BenefitsCellParser,) + blank_empty_parsers}, ] # 25
else:
    cells += [{'name': u'Льготная категория',
            'parsers': (BenefitCategoryCellNumberParser,
                    BenefitCategoryCellTextParser) + none_parsers}, ] #25

cells += [{'name':u'Желаемый ДОУ', 'parsers':
    (IntegerNumberCellParser, MultiSadikNumberCellParser,)
        + blank_empty_parsers}, # 26
    {'name':u'Год начала зачисления', 'parsers':
        (DesiredDateCellNumberParser, DesiredDateCellTextParser)
            + blank_empty_parsers}, # 27
]


class RequestionFormat(Format):

    # xls reading options
    start_line = 2
    cells = cells

    def to_python(self, data_row):
        # Задать год зачисления текущим, если он не указан
        try:
            registration_date = datetime.date(data_row[4], data_row[3], data_row[2])
        except ValueError, e:
            raise ValidationError(u'Неверная дата регистрации: %s' % e)
        try:
            birth_date = datetime.date(data_row[11], data_row[10], data_row[9])
        except ValueError, e:
            raise ValidationError(u'Неверная дата рождения: %s' % e)
        requestion_data = {
            'number_in_old_list': data_row[0],
            'registration_datetime': registration_date,
            'birth_date': birth_date,
            'sex': data_row[12],
            'admission_date': data_row[27],
            'last_name': data_row[6],
            'first_name': data_row[7],
            'patronymic': data_row[8],
            'agent_type': data_row[24],
        }
        requestion_data.update({
            'status':STATUS_REQUESTER,
            'distribute_in_any_sadik': True,
            })
        area = data_row[1]
        if area:
            areas = (area,)
        else:
            areas = ()
        profile_data = {
            'last_name': data_row[21],
            'first_name': data_row[22],
            'patronymic': data_row[23],
            'phone_number': data_row[19],
            'mobile_number': data_row[20]
        }
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
#        в зависимости от реализации либо список льгот, либо категория льгот
        if settings.FACILITY_STORE == settings.FACILITY_STORE_YES:
            benefits = data_row[25]
        else:
            benefit_category = data_row[25]
            if benefit_category is None:
                benefit_category = BenefitCategory.objects.category_without_benefits()
            requestion_data.update({'benefit_category': benefit_category})
            benefits = []
        requestion = Requestion(**requestion_data)
        profile = Profile(**profile_data)
        document = data_row[5]
        return requestion, profile, areas, preferred, address_data, benefits, document
