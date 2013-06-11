# -*- coding: utf-8 -*-
from sadiki.settings import *
from sadiki.conf_settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# INSTALLED_APPS += [
#     'django_extensions',
#     'debug_toolbar',
# #    'sadiki.import_data',
# ]

# MIDDLEWARE_CLASSES += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]
CACHE_BACKEND = "locmem://"

INTERNAL_IPS = ('127.0.0.1',)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
