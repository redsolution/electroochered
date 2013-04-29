# -*- coding: utf-8 -*-
import urllib
import urllib2
from BeautifulSoup import BeautifulStoneSoup
try:
    import simplejson
except ImportError:
    from django.utils import simplejson


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
            precision = soup.ymaps.geoobjectcollection.featuremember.geoobject.metadataproperty.geocodermetadata.precision.string
            if precision == u'number' or precision == u'exact':
                return tuple(soup.ymaps.geoobjectcollection.featuremember.geoobject.point.pos.string.split(' '))


class Google(Geocoder):
    u"""
    Реализация Goole - геокодера, аналогично Яндексу.
    https://developers.google.com/maps/documentation/geocoding/#XML

    В конструктор класса передаются параметры,
    в функцию geocode - строка запроса.

    ``geocode`` возвращает кортеж из координат, либо None
    """
    base_url = 'http://maps.googleapis.com/maps/api/geocode/%(format)s?address=%(query)s&%(encoded_params)s'
    defaults = {
        'format': 'xml',
        'language': 'ru',
        'sensor': 'false',
    }

    def encode_params(self, kwargs):
        kwargs.pop('format')  # убрать формат из строки, т.к. он передается отдельно
        if 'bounds' in kwargs:
            kwargs['bounds'] = '%s,%s|%s,%s' % (kwargs.pop('bounds'))

        return super(Google, self).encode_params(kwargs)

    def parse_response(self, data):
        soup = BeautifulStoneSoup(data)
        if (soup.geocoderesponse.status.string == 'OK'
            and soup.geocoderesponse.result.geometry.location_type.string in ('ROOFTOP', 'RANGE_INTERPOLATED')):
            return (
                soup.geocoderesponse.result.geometry.location.lng.string,
                soup.geocoderesponse.result.geometry.location.lat.string
            )
