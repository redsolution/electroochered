# -*- coding: utf-8 -*-
import datetime
import re
import json
import uuid
import urllib
import urllib2
from os.path import join, split, exists
from os import makedirs
from subprocess import Popen
from collections import OrderedDict
import math

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db.models.aggregates import Min
from django.utils.safestring import mark_safe
from BeautifulSoup import BeautifulStoneSoup

import sadiki.core.models
from pysnippets import gpgtools


def crc2(value):
    result = 0
    if value & ~((1 << 22) - 1):
        raise ValueError
    for x in xrange(22):
        result += (value >> x) & 1
    return result & 3


def add_crc(data):
    value = data & ((1 << 22) - 1)
    crc = crc2(value) << 22
    return value | crc


def remove_crc(data):
    value = data & ((1 << 22) - 1)
    crc = (data >> 22) & 3
    if crc2(value) != crc:
        raise ValueError
    return value


def luhn_sum(s):
    s = str(s)
    total = 0
    evenPos = True
    for d in reversed(s):
        d = int(d)
        assert 0 <= d <= 9
        if evenPos:
            d *= 2
            if d > 9:
                d = (d % 10) + 1
        total += d
        evenPos = not evenPos
    return total


def calculate_luhn_digit(s):
    u"""вычисление контрольной цифры по алгоритму Луна"""
    s = str(s)
    total = luhn_sum(s)
    if not total % 10:
        return 0
    else:
        return 10 - total % 10


def check_luhn(s):
    s = str(s)
    number = s[:-1]
    digit = int(s[-1:])
    total = luhn_sum(number)
    if (total + digit) % 10 == 0:
        return True
    else:
        return False


def get_user_by_email(email):
    # если e-mail уже занят(подтвержден), то возвращает пользователя,
    # иначе None
    if email:
        try:
            user = User.objects.get(profile__email_verified=True, email=email)
        except User.DoesNotExist:
            return None
        else:
            return user
    return None


def get_unique_username():
    """Returns uuid generated 30-character string"""
    s = unicode(uuid.uuid4())
    s = s.replace('-', '')[:30]
    return s


def scheme_and_domain():
    """Returns dictionary with URL scheme and site domain"""
    return {
        'scheme': getattr(settings, "DEFAULT_HTTP_PROTOCOL", "http"),
        'domain': Site.objects.get_current(),
    }


def check_url(url, default=None):
#    copy from django code (django.contrib.auth.views login)
    if not url or ' ' in url:
        url = default
        # Heavier security check -- redirects to http://example.com should 
        # not be allowed, but things like /view/?param=http://example.com 
        # should be allowed. This regex checks if there is a '//' *before* a
        # question mark.
    elif '//' in url and re.match(r'[^\?]*//', url):
        url = default
    return url


def get_distribution_year():
    u"""
    Возвращает учебный год в формате даты(число и месяц = 1 января)
    согласно настройке ``NEW_YEAR_START``
    Если у текущей даты число и месяц превосходят ``NEW_YEAR_START``, то
    возвращается текущий год, иначе предшествующий
     """

    current_date = datetime.date.today()
    ny_date = settings.NEW_YEAR_START.replace(year=current_date.year).date()

    if current_date <= ny_date:
        distribution_year_start = datetime.date(current_date.year - 1, 1, 1)
    else:
        distribution_year_start = datetime.date(current_date.year, 1, 1)

    return distribution_year_start


def get_current_distribution_year():
    u"""
    Возвращается текущий учебный год в формате даты(число и месяц = 1 января),
    принимая во внимание активные группы.

    Т.е. ``get_current_distribution_year`` может возвратить прошлый учебный год,
    если группы прошлого года ещё не закрыты.

    В случае если групп нет, возвращается текущий учебный год согласно
    настройкам.
    """
    from sadiki.core.models import SadikGroup
    if SadikGroup.objects.active().exists():
        curr_date = SadikGroup.objects.active().aggregate(Min('year'))['year__min']
        return curr_date.replace(day=1, month=1)
    else:
        return get_distribution_year()


def get_qs_attr(instance, attr, default=None):
    if '__' in attr:
        obj_attr, new_attr = attr.split('__')
        return get_qs_attr(getattr(instance, obj_attr), new_attr, default)
    else:
        return getattr(instance, attr, default)


def run_command(command_name, *args):
    u"""Запускает в фоне management-команду"""
    # если тестируем, то запуск должен отличаться
    #if sys.argv[1] == 'test':
    #    management.call_command(command_name, *args)
    #else:
    manage_file = join(settings.PROJECT_DIR, 'manage.py')
    lockname = join(settings.LOCK_DIR,
                    command_name.replace(' ', '-').replace('/', '-'))
    if not exists(settings.LOCK_DIR):
        makedirs(settings.LOCK_DIR)
    cmd_line = 'flock -n %(lockname)s -c "python %(manage_file)s %(command)s %(args)s"' % {
        'lockname': lockname,
        'manage_file': manage_file,
        'command': command_name,
        'args': u' '.join(args),
    }
    return Popen(cmd_line, shell=True)


def get_openlayers_js():
    u"""Возвращает media для отображения openlayers(берется из админки)"""
    from sadiki.core.admin import CustomGeoAdmin
    media = forms.Media()
    media.add_js([CustomGeoAdmin.openlayers_url])
    media.add_js(CustomGeoAdmin.extra_js)
    return mark_safe(media)


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
    Формат аргмуента: кортеж из четырёх значений коодинат, например,
    (lat1, lng1, lat2, lng2)
    """
    base_url = 'http://geocode-maps.yandex.ru/1.x/?geocode=%(query)s&%(encoded_params)s'
    defaults = {
        'format': 'xml',
    }

    def encode_params(self, kwargs):
        if 'bounds' in kwargs:
            x1, y1, x2, y2 = kwargs.pop('bounds')
            ll = ((x1+x2)/2, (y1+y2)/2)  # координаты центра области
            # протяженность области в градусах
            spn = (abs(ll[0] - x1), abs(ll[1] - y1))

            kwargs['ll'] = '%f,%f' % ll
            kwargs['spn'] = '%f,%f' % spn

        return super(Yandex, self).encode_params(kwargs)

    def parse_response(self, data):
        soup = BeautifulStoneSoup(data)
        found = soup.ymaps.geoobjectcollection.metadataproperty.geocoderresponsemetadata.found.string
        if found != '0':
            return tuple(soup.ymaps.geoobjectcollection.featuremember.geoobject.point.pos.string.split(' '))


def get_coords_from_address(address):
    geocoder = Yandex()
    coords = geocoder.geocode(address)
    return coords


def create_xls_report(response, requestions_by_sadiks ,distribution):
    file_name = u'Raspredelenie_%s' % (distribution.end_datetime.strftime('%d-%m-%Y_%H-%M'))
    response['Content-Disposition'] = u'attachment; filename="%s.xls"' % file_name
    import xlwt
    style = xlwt.XFStyle()
    style.num_format_str = 'DD-MM-YYYY'
    header_style = xlwt.easyxf('font: bold 1')
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet(u'Результаты распределения')
    header = [
        u'Номер заявки',
        u'Номер в списке',
        u'Дата рождения',
        u'Адрес',
        u'Группа',
        u'Документ',
    ]
    if settings.USE_DISTRICTS:
        header.insert(4, u'Район')
    else:
        header.insert(4, u'Группа ДОУ')
    row_number = 0
    for requestions_by_sadik in requestions_by_sadiks:
        if requestions_by_sadik[1]:
            ws.write_merge(row_number, row_number, 0, 4,
                           requestions_by_sadik[0].name, header_style)
            row_number += 1
            for column_number, element in enumerate(header):
                ws.write(row_number, column_number, element, header_style)
            row_number += 1
            for requestion in requestions_by_sadik[1]:
                row = [requestion.requestion_number,
                       requestion.number_in_old_list,
                       requestion.birth_date,
                       requestion.location_properties,
                       unicode(requestion.distributed_in_vacancy.sadik_group)]
                if settings.USE_DISTRICTS:
                    if requestion.district:
                        row.insert(4, requestion.district.title)
                    else:
                        row.insert(4, '')
                else:
                    row.insert(4, requestions_by_sadik[0].area.name)
                if requestion.related_documents:
                    document = requestion.related_documents[0]
                    row.append("%s (%s)" % (document.document_number,
                                            document.template.name))
                for column_number, element in enumerate(row):
                    ws.write(row_number, column_number, element, style)
                row_number += 1
    ws.col(0).width = 256 * 20
    ws.col(3).width = 256 * 30
    ws.col(4).width = 256 * 30
    ws.col(5).width = 256 * 35
    ws.col(6).width = 256 * 45

    if settings.USE_DISTRICTS:
        districts = sadiki.core.models.District.objects.all().order_by('title')
        for district in districts:
            row_number = 0
            ws = wb.add_sheet(district.title)
            header[4] = u'ДОУ'
            for column_number, element in enumerate(header):
                ws.write(row_number, column_number, element, header_style)
            row_number += 1
            for requestions_by_sadik in requestions_by_sadiks:
                if requestions_by_sadik[1]:
                    for requestion in requestions_by_sadik[1]:
                        if requestion.district == district:
                            row = [requestion.requestion_number,
                                   requestion.number_in_old_list,
                                   requestion.birth_date,
                                   requestion.location_properties,
                                   requestions_by_sadik[0].short_name,
                                   unicode(requestion.distributed_in_vacancy.sadik_group)]
                            if requestion.related_documents:
                                document = requestion.related_documents[0]
                                row.append("%s (%s)" % (document.document_number,
                                                        document.template.name))
                            for column_number, element in enumerate(row):
                                ws.write(row_number, column_number,
                                         element, style)
                            row_number += 1
            ws.col(0).width = 256 * 20
            ws.col(3).width = 256 * 30
            ws.col(4).width = 256 * 30
            ws.col(5).width = 256 * 35
            ws.col(6).width = 256 * 45
    wb.save(response)


def create_xls_from_queue(response, queue):
    reqs = queue.select_related('areas', 'benefit_category')
    file_name = u'Filter_results'
    response['Content-Disposition'] = u'attachment; filename="%s.xls"' % file_name
    import xlwt
    style = xlwt.XFStyle()
    style.num_format_str = 'DD-MM-YYYY'
    header_style = xlwt.easyxf('font: bold 1')
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet(u'Результаты фильтра')
    header = [
        u'Номер заявки',
        u'Дата рождения',
        u'Дата регистрации',
        u'Адрес',
        u'Категория льгот',
        u'Группа',
        u'Желаемый год поступления',
        u'Статус заявки',
        u'Группы ДОУ',
    ]
    row_number = 0
    for column_number, element in enumerate(header):
        ws.write(row_number, column_number, element, header_style)
    row_number += 1
    age_groups = sadiki.core.models.AgeGroup.objects.all()
    current_distribution_year = get_current_distribution_year()
    for requestion in reqs:
        try:
            age_groups_calculated = requestion.age_groups(
                age_groups=age_groups,
                current_distribution_year=current_distribution_year
            )[0].short_name
        except IndexError:
            age_groups_calculated = ''
        row = [
            requestion.requestion_number,
            requestion.birth_date,
            requestion.registration_datetime,
            requestion.location_properties,
            requestion.benefit_category.name,
            age_groups_calculated,
            requestion.admission_date,
            requestion.get_status_display(),
            '; '.join([area.name for area in requestion.areas.all()]),
        ]
        for column_number, element in enumerate(row):
            ws.write(row_number, column_number, element, style)
        row_number += 1
    ws.col(0).width = 256 * 20
    ws.col(3).width = 256 * 30
    ws.col(4).width = 256 * 20
    ws.col(7).width = 256 * 25
    ws.col(8).width = 256 * 200
    wb.save(response)


def get_random_token():
    return str(uuid.uuid4())


def find_closest_kg(requestion, save=True, verbose=False):
    kgs = sadiki.core.models.Sadik.objects.filter(
        area__in=requestion.areas.all(),
        active_registration=True,
        active_distribution=True).select_related('address')
    closest = None
    if not kgs:
        if verbose:
            print "Empty kindergarten set for {}".format(requestion)
        return None
    for kg in kgs:
        if kg.address.coords:
            distance = measure_distance(requestion.location, kg.address.coords)
            if not closest or closest['distance'] > distance:
                closest = {'kg': kg, 'distance': distance}
        else:
            closest = {'kg': kg, 'distance': 0}
    requestion.closest_kg = closest['kg']
    if save:
        requestion.save()


def measure_distance(coords1, coords2):

    lat1 = coords1[0]
    lon1 = coords1[1]
    lat2 = coords2[0]
    lon2 = coords2[1]

    EARTH_RADIUS = 6378.137
    dLat = (lat2 - lat1) * math.pi / 180
    dLon = (lon2 - lon1) * math.pi / 180
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = EARTH_RADIUS * c
    return d * 1000  # meters


def make_error_msg(errors):
    u"""
    Функция возвращает все ошибки, возникшие при за полнении формы, в виде
    одной строки.

    Параметр errors - объект form.errors
    """
    msg = u""
    for error in errors:
        field_errors = u""
        for field_error in errors[error]:
            field_errors = field_errors + field_error + ' '
        msg += u"{}: {}\n".format(error, field_errors)
    return msg


def get_child_from_es(birth_cert):
    u"""
    Получаем по свидетельству о рожденнии данные о ребенке из Электросада.
    """
    # во время тестирования api ЭС недоступно, возвращаем "dummy" объект
    if settings.TEST_MODE:
        return []
    post_data = gpgtools.get_signed_json({'birth_cert': birth_cert})
    domain = settings.ES_DOMAIN
    if not domain:
        site = Site.objects.get_current()
        domain = site.domain.split('.')[0] + '.electrosadik.ru'
    url = "http://{}/api/base/get_child_by_birth_cert/".format(domain)

    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, post_data).read()
    decrypted_data = gpgtools.decrypt_data(response)
    return json.loads(decrypted_data)


def active_child_exist(birth_cert):
    u"""
    Проверяем, если ли в ЭС активные дети с заданным свидетельством о рождении
    """
    # во время тестирования api ЭС недоступно, возвращаем "dummy" объект
    if settings.TEST_MODE:
        return False
    try:
        child_data = get_child_from_es(birth_cert)
    except Exception:
        from sadiki.core.exceptions import TransitionNotAllowed
        raise TransitionNotAllowed(
            u"Ошибка при проверке номера документа в Электросаде, "
            u"повторите попытку позднее")
    from sadiki.api.views import STATUS_OK
    from sadiki.api.utils import is_active_child_status
    if child_data['status_code'] == STATUS_OK and 'status' in child_data['data']:
        if is_active_child_status(child_data['data']['status']):
            return True
    return False


def reorder_fields(fields, order, remove=False):
    u"""
    Переопределяет порядок полей формы.
    При remove=False поля, не указанные в order, будут размещены в конце списка
    При remove=True неуказанные поля будут удалены без возможности наследования
    """
    if remove:
        for field_name, field in fields.items():
            if field_name not in order:
                del fields[field_name]
    else:
        order.extend([key for key in fields.keys() if key not in order])
    return OrderedDict(
        sorted(fields.items(), key=lambda k: order.index(k[0])))


def remove_empty_personal_data_values(data):
    target_keys = [key for key in data if data[key] == '' or data[key] == None]
    for key in target_keys:
        data.pop(key)


def get_fixture_chunk_file_name(base_file_name, chunk_number):
    u"""
    К основному имени файла добавляет номер чанка, с учётом формата файла
    Например, dumps/file.djson.gz => dumps/file.part5.djson.gz
    """
    full_name = list(split(base_file_name))
    concrete_fname = full_name[-1]
    parts = concrete_fname.rsplit('.', 2)
    parts.insert(1, 'part{}'.format(chunk_number))
    full_name[-1] = '.'.join(parts)
    return join(*full_name)
