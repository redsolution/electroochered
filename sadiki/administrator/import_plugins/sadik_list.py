# -*- coding: utf-8 -*-
from django.contrib.gis.geos import Point
from sadiki.administrator.models import Format
from sadiki.administrator.parsers import IntegerNumberCellParser, TextCellParser, \
    TextNumberCellParser, blank_empty_parsers, IntegerTextCellParser, TextDecimalNumberCellParser, AreaCellParser, PostIndexIntegerCellParser, PostIndexTextCellParser, AgeGroupCellParser, blank_parsers, DecimalNumberCellParser, DecimalTextCellParser
from sadiki.core.models import Sadik, AgeGroup


sadik_list_cells = (
    {'name':u'Территориальная область', 'parsers':(AreaCellParser,)}, # 0
    {'name':u'Полное название', 'parsers': (TextCellParser,)}, # 1
    {'name':u'Короткое название', 'parsers': (TextCellParser,)}, # 2
    {'name':u'Номер', 'parsers': (IntegerNumberCellParser, IntegerTextCellParser)}, # 3

#    директор
    {'name':u'Фамилия директора', 'parsers':
        (TextCellParser,) + blank_empty_parsers}, # 4
    {'name':u'Имя директора', 'parsers':
        (TextCellParser,) + blank_empty_parsers}, # 5
    {'name':u'Отчество директора', 'parsers':
        (TextCellParser,) + blank_empty_parsers}, # 6

#    адрес
    {'name':u'Адрес: почтовый индекс', 'parsers':
        (PostIndexIntegerCellParser, PostIndexTextCellParser)}, # 7
    {'name':u'Адрес: номер квартала', 'parsers':
        (TextCellParser, TextNumberCellParser)+blank_empty_parsers}, # 8
    {'name':u'Адрес: улица', 'parsers':
        (TextCellParser,)}, # 9
    {'name':u'Адрес: дом', 'parsers':
        (TextCellParser, TextDecimalNumberCellParser) + blank_empty_parsers}, # 10

#дополнительная информация
    {'name':u'Телефон', 'parsers':
        (TextCellParser, TextDecimalNumberCellParser,) + blank_empty_parsers}, # 11
    {'name':u'Адрес сайта', 'parsers':
        (TextCellParser, ) + blank_empty_parsers}, # 12
    {'name':u'Адрес электронной почты', 'parsers':
        (TextCellParser, ) + blank_parsers}, # 13
    {'name':u'Техническая оснащенность', 'parsers':
        (TextCellParser, ) + blank_empty_parsers}, # 14
    {'name':u'Учебные программы дополнительного образования', 'parsers':
        (TextCellParser, ) + blank_empty_parsers}, # 15

#возрастные группы
    {'name':u'Возрастные группы', 'parsers': (AgeGroupCellParser,) + blank_empty_parsers}, # 16
    {'name':u'Широта', 'parsers': (DecimalNumberCellParser, DecimalTextCellParser)}, # 17
    {'name':u'Долгота', 'parsers': (DecimalNumberCellParser, DecimalTextCellParser)}, # 18
)

class SadikListFormat(Format):

    # xls reading options
    start_line = 2
    cells = sadik_list_cells

    def to_python(self, data_row):
        last_name = data_row[4]
        first_name = data_row[5]
        patronymic = data_row[6]
        full_name = ' '.join([el for el in (last_name, first_name, patronymic) if el])
        sadik = Sadik(
            area=data_row[0],
            name=data_row[1],
            short_name=data_row[2],
            number=data_row[3],
            head_name=full_name,
            phone=data_row[11],
            site=data_row[12],
            email=data_row[13],
            tech_level=data_row[14],
            training_program=data_row[15],
        )
        latitude = data_row[17]
        longtitude = data_row[18]
        address_data = {
            'postindex': data_row[7],
            'block_number': data_row[8],
            'street': data_row[9],
            'building_number': data_row[10],
            'coords': Point(longtitude, latitude)
            }
        age_groups = data_row[16] or AgeGroup.objects.all()
        return sadik, address_data, age_groups
