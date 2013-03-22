# -*- coding: utf-8 -*-
import os
gettext_noop = lambda s: s
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))

#ADMINS = (
#    ('src', 'src@redsolution.ru'),
#)
#
#MANAGERS = ADMINS

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.contrib.gis.db.backends.postgis',
#        'NAME': 'sadiki3',
#        'USER': 'sadiki3',
#        'PASSWORD': DATABASE_PASSWORD,
#        'HOST': 'localhost',
#        'PORT': '5432',
#    }
#}

TIME_ZONE = None

LANGUAGE_CODE = 'ru'

SITE_ID = 1
EMAIL_SUBJECT_PREFIX = '[sadiki]'
DEFAULT_FROM_EMAIL = 'noreply@example.com'
SERVER_EMAIL = 'sadiki3'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
#USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

UPLOAD_ROOT = os.path.join(MEDIA_ROOT, 'upload')
UPLOAD_DIR = 'upload'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
UPLOAD_URL = MEDIA_URL + UPLOAD_DIR

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'


MIDDLEWARE_CLASSES = [
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sadiki.core.middleware.NoCacheMiddleware',
    'sadiki.core.middleware.SettingsJSMiddleware',
#    'sadiki.core.middleware.LogPIDMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]

ROOT_URLCONF = 'sadiki.urls'


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    'django.contrib.gis',
    'sadiki.core',
    'sadiki.account',
    'sadiki.authorisation',
    'sadiki.operator',
    'sadiki.administrator',
    'sadiki.anonym',
    'sadiki.supervisor',
    'sadiki.logger',
    'sadiki.statistics',
    'sadiki.distribution',
    'sadiki.custom_flatpages',
#    'sadiki.feedback',
    'south',
    'pytils',
#    'tastypie',
    'zenforms',
    'chunks',
    'tinymce',
    'trustedhtml',
    'attachment',
]

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
)

STATICFILES_DIRS = (
    MEDIA_ROOT,
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    )

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.i18n',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.csrf',
    'sadiki.core.context_processors.constants',
    'sadiki.core.context_processors.municipality_settings',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'sadiki.authorisation.backends.EmailAuthBackend',
)
AUTH_PROFILE_MODULE = 'core.Profile'

LOGIN_REDIRECT_URL = '/'

DATE_FORMAT = 'Y-m-d'
JS_DATE_FORMAT = 'yy-mm-dd'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = 'Y-m-d H:i'
SHORT_DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i'
DATE_INPUT_FORMATS = ('%Y-%m-%d', "%Y/%m/%d")

#Session settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ------ TinyMCE ------

TINYMCE_JS_URL = '%stiny_mce/tiny_mce.js' % STATIC_URL

TINYMCE_DEFAULT_CONFIG = {
    'mode': 'exact',
    'theme': 'advanced',
    'relative_urls': False,
    'width': 600,
    'height': 300,
    'plugins': 'table,advimage,advlink,inlinepopups,preview,media,searchreplace,contextmenu,paste,fullscreen,noneditable,visualchars,nonbreaking,xhtmlxtras',
    'theme_advanced_buttons1': 'fullscreen,|,bold,italic,underline,strikethrough,|,sub,sup,|,bullist,numlist,|,outdent,indent,|,formatselect,removeformat',
    'theme_advanced_buttons2': 'cut,copy,paste,pastetext,pasteword,|,search,replace,|,undo,redo,|,link,unlink,anchor,image,media,charmap,|,visualchars,nonbreaking',
    'theme_advanced_buttons3': 'visualaid,tablecontrols,|,blockquote,del,ins,|,preview,code',
    'theme_advanced_toolbar_location': 'top',
    'theme_advanced_toolbar_align': 'left',
    'extended_valid_elements': 'noindex',
    'custom_elements': 'noindex',
    'external_image_list_url': 'images/',
    'external_link_list_url': 'links/',
}

#attachment прикреплен к Chunk через админку, т.к. не нашел поддержки второй админки в настройках приложения
ATTACHMENT_FOR_MODELS = []
ATTACHMENT_IKSPECS = 'sadiki.attachment_ikspecs'


POSTGIS_VERSION = (1, 4, 0)
LOCK_DIR = os.path.join(PROJECT_DIR, 'lock')
