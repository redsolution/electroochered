# -*- coding: utf-8 -*-
import os
gettext_noop = lambda s: s
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))

TIME_ZONE = 'Asia/Yekaterinburg'

LANGUAGE_CODE = 'ru'

SITE_ID = 1
DEFAULT_FROM_EMAIL = 'noreply@example.com'
SERVER_EMAIL = 'sadiki3'

# Флаг, используемый для отключения запросов ко внешним api-сервисам во время
# тестирования
TEST_MODE = False

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

IMPORT_STATIC_DIR = 'import_files'
SECURE_STATIC_ROOT = os.path.join(PROJECT_DIR, 'secure_static')

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
    'django.middleware.common.CommonMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sadiki.core.middleware.NoCacheMiddleware',
    'sadiki.core.middleware.SettingsJSMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'sadiki.social_auth_custom.middleware.SocialAuthExceptionMiddlewareCustom',
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
    'sadiki.api',
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
    'sadiki.social_auth_custom',
    'pytils',
    'zenforms',
    'chunks',
    'tinymce',
    'trustedhtml',
    'social.apps.django_app.default',
    'attachment',
    'hex_storage',
    'rest_framework',
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
    'sadiki.core.context_processors.get_notifier',
    'sadiki.core.context_processors.get_special_apps',
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
)

AUTHENTICATION_BACKENDS = (
    'sadiki.social_auth_custom.backends.vk_custom.VKOAuth2Custom',
    'django.contrib.auth.backends.ModelBackend',
    'sadiki.authorisation.backends.EmailAuthBackend',
)
AUTH_PROFILE_MODULE = 'core.Profile'

LOGIN_REDIRECT_URL = '/'

DATE_FORMAT = 'd.m.Y'
JS_DATE_FORMAT = 'dd.mm.yy'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = 'd.m.Y H:i'
SHORT_DATE_FORMAT = 'd.m.Y'
DATE_INPUT_FORMATS = ('%d.%m.%Y', "%Y/%m/%d")

LOGIN_URL = '/auth/login/'

#Session settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ------ trustedhtml ------

# Object tags (swf players an so on) from these sites are allowed
TRUSTEDHTML_OBJECT_SITES = [
    'youtube.com',
    'www.youtube.com',
]

# ------ TinyMCE ------

TINYMCE_JS_URL = os.path.join(STATIC_URL, 'tiny_mce/tiny_mce.js')
TINYMCE_JS_ROOT = os.path.join(STATIC_ROOT, 'tiny_mce')
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
    'custom_elements': 'noindex',
    'external_image_list_url': 'images/',
    'external_link_list_url': 'links/',
    'extended_valid_elements': 'noindex,iframe[src|style|width|height|scrolling|marginwidth|marginheight|frameborder]',
}

#attachment прикреплен к Chunk через админку, т.к. не нашел поддержки второй админки в настройках приложения
ATTACHMENT_FOR_MODELS = []
ATTACHMENT_IKSPECS = 'sadiki.attachment_ikspecs'


POSTGIS_VERSION = (1, 4, 0)
LOCK_DIR = os.path.join(PROJECT_DIR, 'lock')

REQUESTER_USERNAME_PREFIX = 'requester'

SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['username', 'email', 'first_name', 'last_name', ]

VK_EXTRA_SCOPE = ['offline', ]
VK_EXTRA_DATA = ['contacts', 'connections', ]

SOCIAL_AUTH_URL_NAMESPACE = 'social_auth'

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'sadiki.social_auth_custom.pipeline.auth.social_user',
    'social.pipeline.user.get_username',
    'sadiki.social_auth_custom.pipeline.auth.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'sadiki.social_auth_custom.pipeline.auth.update_user_info',
)

SOCIAL_AUTH_DISCONNECT_PIPELINE = (
    'sadiki.social_auth_custom.pipeline.disconnect.get_user_for_disconnect',
    'social.pipeline.disconnect.allowed_to_disconnect',
    'social.pipeline.disconnect.get_entries',
    'social.pipeline.disconnect.revoke_tokens',
    'social.pipeline.disconnect.disconnect'
)


LOGIN_ERROR_URL = '/auth/login/'

DEFAULT_FILE_STORAGE = 'hex_storage.HexFileSystemStorage'
