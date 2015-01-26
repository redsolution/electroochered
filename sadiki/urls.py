# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import patterns, include, handler500, handler404, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from sadiki.administrator.admin import site as sadiki_admin_site
from sadiki.core.views import VkontakteFrame
from sadiki.plugins import plugins, SadikiPlugin

admin.autodiscover()

handler500  # Pyflakes
handler404

urlpatterns = patterns('',)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns(
        '',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )

if 'smevfms' in settings.INSTALLED_APPS:
    urlpatterns += patterns(
        '',
        (r'^fms/', include('smevfms.urls')),
    )

if 'smevzags' in settings.INSTALLED_APPS:
    urlpatterns += patterns(
        '',
        (r'^zags/', include('smevzags.urls')),
    )

if 'electroochered-authesia' in settings.INSTALLED_APPS:
    urlpatterns += patterns(
        '',
        (r'^esia_auth/', include('electroochered-authesia.urls')),
    )

if 'electrostat' in settings.INSTALLED_APPS:
    urlpatterns += patterns(
        '',
        (r'^api/', include('electrostat.urls')),
    )

urlpatterns += patterns(
    '',
    (r'^adm/', include(sadiki_admin_site.urls)),
    (r'^api2/', include('sadiki.api.urls')),
    (r'^auth/', include('sadiki.authorisation.urls')),
    (r'^social_auth/', include('sadiki.social_auth_custom.urls')),
    (r'^account/', include('sadiki.account.urls')),
    (r'^operator/', include('sadiki.operator.urls')),
    (r'^distribution/', include('sadiki.distribution.urls')),
    (r'^anonym/', include('sadiki.anonym.urls')),
    (r'^supervisor/', include('sadiki.supervisor.urls')),
    (r'^logs/', include('sadiki.logger.urls')),
    (r'^statistics/', include('sadiki.statistics.urls')),
    (r'^', include('sadiki.core.urls')),
    (r'^robots.txt$', 'django.views.generic.simple.direct_to_template',
        {'template': 'robots.txt', 'mimetype': 'text/plain'}),
    (r'^tinymce/', include('tinymce.urls')),
    url(r'^vk/', VkontakteFrame.as_view(), name='vk_app'),
    url(r'^admin/', include(admin.site.urls)),
)

for plugin in plugins:
    if isinstance(plugin, SadikiPlugin):
        try:
            urlpatterns += plugin.get_urls()
        except NotImplementedError:
            pass
