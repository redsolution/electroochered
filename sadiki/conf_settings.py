# -*- coding: utf-8 -*-
from ConfigParser import RawConfigParser
from core.settings import *
from datetime import datetime
from os.path import join, expanduser
import re

config = RawConfigParser()
config.read(expanduser(join('~', '.config', 'electroochered', 'electroochered.conf')))


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
DATABASE_USER = config.get('core', 'DATABASE_USER')
DATABASE_PASSWORD = config.get('core', 'DATABASE_PASSWORD')
DATABASE_HOST = config.get('core', 'DATABASE_HOST')
DATABASE_PORT = config.get('core', 'DATABASE_PORT')
DATABASE_NAME = config.get('core', 'DATABASE_NAME')

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
SECRET_KEY = config.get('core', 'SECRET_KEY')

# [maps]
MAP_CENTER = config.get('core', 'MAP_CENTER')
MAP_ZOOM = config.getint('core', 'MAP_ZOOM')
LEAFLET_TILES_URL = config.get('core', 'TILES_URL')
LEAFLET_TILES_SUBDOMAINS = aslist(config.get('core', 'TILES_SUBDOMAINS'))
OPENLAYERS_URLS = get_openlayers_urls(LEAFLET_TILES_URL, LEAFLET_TILES_SUBDOMAINS)

# [options]
MUNICIPALITY_OCATO = config.getint('core', 'MUNICIPALITY_OCATO')
EMAIL_KEY_VALID = config.getint('core', 'EMAIL_KEY_VALID')
MAX_CHILD_AGE = config.getint('core', 'MAX_CHILD_AGE')
# Например 17 Jul
new_year_start_config = config.get('core', "NEW_YEAR_START").split()
NEW_YEAR_START = datetime(
    year=1900, month=int(new_year_start_config[1]), day=int(new_year_start_config[0]))
APPEAL_DAYS = config.getint('core', 'APPEAL_DAYS')

DESIRED_DATE = config.getint('core', 'DESIRED_DATE')
DESIRED_SADIKS = config.getint('core', 'DESIRED_SADIKS')
FACILITY_STORE = config.getint('core', 'FACILITY_STORE')
TEMP_DISTRIBUTION = config.getint('core', 'TEMP_DISTRIBUTION')
IMMEDIATELY_DISTRIBUTION = config.getint("core", "IMMEDIATELY_DISTRIBUTION")
ETICKET = config.getint("core", "ETICKET")
#переходы, которые особо отображаются в очереди
SPECIAL_TRANSITIONS = [int(transition) for transition in config.get("core", "SPECIAL_TRANSITIONS").split(',')]
#название типа документа, которое используется при импорте
DEFAULT_IMPORT_DOCUMENT_NAME = config.get('core', 'DEFAULT_IMPORT_DOCUMENT_NAME')
# название области, используется при импорте
REGION_NAME = config.get('core', 'REGION_NAME').decode('utf-8')
# маска для номера заявки(используется в модуле для jquery)
REQUESTION_NUMBER_MASK = config.get('core', 'REQUESTION_NUMBER_MASK').decode('utf-8')
# авторизация через ВКонтакте
VK_APP_ID = config.get('vkontakte', 'VK_APP_ID')
VK_API_SECRET = config.get('vkontakte', 'VK_API_SECRET')

USE_DISTRICTS = config.getint('core', 'USE_DISTRICTS')

if config.has_option('core', 'ES_DOMAIN'):
    ES_DOMAIN = config.get('core', 'ES_DOMAIN')
else:
    ES_DOMAIN = None

# [email]
EO_USER = REGION_NAME.split(',')[-1].strip()
SERVER_EMAIL = u'Место в садик ({}) <{}>'.format(
    EO_USER, config.get('core', 'SERVER_EMAIL'))
EMAIL_SUBJECT_PREFIX = '{}: '.format(DATABASE_USER)
DEFAULT_FROM_EMAIL = u'Место в садик ({}) <{}>'.format(
    EO_USER, config.get('core', 'DEFAULT_FROM_EMAIL'))
ADMINS = ((DATABASE_USER, config.get('core', 'WEBMASTER')), )
MANAGERS = (config.get('core', 'STUFF'), )
