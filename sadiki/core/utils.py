# -*- coding: utf-8 -*-
from os.path import join, exists
from os import makedirs
from subprocess import Popen
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
import datetime
import re
import uuid
import urllib
import urllib2
from BeautifulSoup import BeautifulStoneSoup

from django.db.models.aggregates import Min
from django.utils.safestring import mark_safe


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

    В случае если групп нет, возвращается текущий учебный год согласно настройкам.
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
#    если тестируем, то запуск должен отличаться
    #if sys.argv[1] == 'test':
    #    management.call_command(command_name, *args)
    #else:
    manage_file = join(settings.PROJECT_DIR, 'manage.py')
    lockname = join(settings.LOCK_DIR, command_name.replace(' ', '-').replace('/', '-'))
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


def get_coords_from_address(address):
    geocoder = Yandex()
    coords = geocoder.geocode(address)
    return coords