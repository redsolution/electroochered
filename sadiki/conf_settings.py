# -*- coding: utf-8 -*-
from ConfigParser import RawConfigParser
from core.settings import *
from datetime import datetime
from os.path import join, abspath, dirname
import re

config = RawConfigParser()
config.read(join(dirname(dirname(abspath(__file__))), 'defaults.cfg'))
config.read(join(dirname(dirname(abspath(__file__))),
    'eturn-django-settings.ini'))


# get from pyramid
def aslist_cronly(value):
    if isinstance(value, basestring):
        value = filter(None, [x.strip() for x in value.splitlines()])
    return list(value)

def aslist(value, flatten=True):
    """ Return a list of strings, separating the input based on newlines
    and, if flatten=True (the default), also split on spaces within
    each line."""
    values = aslist_cronly(value)
    if not flatten:
        return values
    result = []
    for value in values:
        subvalues = value.split()
        result.extend(subvalues)
    return result

def get_openlayers_urls(leaflet_url, leaflet_subdomains=None):
    url = re.sub('{[a-z]}', lambda matchgroup: '$'+matchgroup.group(0),
        leaflet_url)
    if "${s}" in url:
        openlayers_urls = []
        for subdomain in leaflet_subdomains:
            url_with_subdomain = url.replace("${s}", subdomain)
            openlayers_urls.append(url_with_subdomain)
        return openlayers_urls
    else:
        return [url,]

# [database]
DATABASE_USER = config.get('database', 'DATABASE_USER')
DATABASE_PASSWORD = config.get('database', 'DATABASE_PASSWORD')
DATABASE_HOST = config.get('database', 'DATABASE_HOST')
DATABASE_PORT = config.get('database', 'DATABASE_PORT')
DATABASE_NAME = config.get('database', 'DATABASE_NAME')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': DATABASE_PORT,
    }
}

# [secrets]
SECRET_KEY = config.get('secrets', 'SECRET_KEY')

# [email]
SERVER_EMAIL = config.get('email', 'SERVER_EMAIL')
DEFAULT_FROM_EMAIL = config.get('email', 'DEFAULT_FROM_EMAIL')
ADMINS = tuple(config.items('admin mail'))
MANAGERS = tuple(config.items('stuff mail'))

# [maps]
MAP_CENTER = config.get('map', 'MAP_CENTER')
MAP_ZOOM = config.getint('map', 'MAP_ZOOM')
LEAFLET_TILES_URL = config.get('map', 'TILES_URL')
LEAFLET_TILES_SUBDOMAINS = aslist(config.get('map', 'TILES_SUBDOMAINS'))
OPENLAYERS_URLS = get_openlayers_urls(LEAFLET_TILES_URL, LEAFLET_TILES_SUBDOMAINS)

# [options]
MUNICIPALITY_OCATO = config.getint('options', 'MUNICIPALITY_OCATO')
EMAIL_KEY_VALID = config.getint('options', 'EMAIL_KEY_VALID')
MAX_CHILD_AGE = config.getint('options', 'MAX_CHILD_AGE')
# Например 17 Jul
new_year_start_config = config.get('options', "NEW_YEAR_START").split()
NEW_YEAR_START = datetime(
    year=1900, month=int(new_year_start_config[1]), day=int(new_year_start_config[0]))
APPEAL_DAYS = config.getint('options', 'APPEAL_DAYS')

DESIRED_DATE = config.getint('options', 'DESIRED_DATE')
DESIRED_SADIKS = config.getint('options', 'DESIRED_SADIKS')
FACILITY_STORE = config.getint('options', 'FACILITY_STORE')
TEMP_DISTRIBUTION = config.getint('options', 'TEMP_DISTRIBUTION')
IMMEDIATELY_DISTRIBUTION = config.getint("options", "IMMEDIATELY_DISTRIBUTION")
ETICKET = config.getint("options", "ETICKET")
#переходы, которые особо отображаются в очереди
SPECIAL_TRANSITIONS = [int(transition) for transition in config.get("options", "SPECIAL_TRANSITIONS").split(',')]
#название типа документа, которое используется при импорте
DEFAULT_IMPORT_DOCUMENT_NAME = config.get('options', 'DEFAULT_IMPORT_DOCUMENT_NAME')
