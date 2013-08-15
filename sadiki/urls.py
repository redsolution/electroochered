# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import patterns, include, handler500, handler404
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.conf.urls.defaults import patterns, url
from sadiki.administrator.admin import site as sadiki_admin_site
from sadiki.core.views import VkontakteFrame

admin.autodiscover()

handler500 # Pyflakes
handler404

urlpatterns = patterns('',)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )

urlpatterns += patterns(
    '',
    (r'^adm/', include(sadiki_admin_site.urls)),
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
)
