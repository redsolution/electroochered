# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import include, handler500, handler404, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.views.generic.base import TemplateView
from sadiki.administrator.admin import site as sadiki_admin_site
from sadiki.core.views import VkontakteFrame
from sadiki.plugins import plugins, SadikiPlugin

handler500  # Pyflakes
handler404

urlpatterns = [
    url(r'^adm/', include(sadiki_admin_site.urls)),
    url(r'^api2/', include('sadiki.api.urls')),
    url(r'^auth/', include('sadiki.authorisation.urls')),
    url(r'^social_auth/', include('sadiki.social_auth_custom.urls',
                                  namespace='social_auth')),
    url(r'^account/', include('sadiki.account.urls')),
    url(r'^operator/', include('sadiki.operator.urls')),
    url(r'^distribution/', include('sadiki.distribution.urls')),
    url(r'^anonym/', include('sadiki.anonym.urls')),
    url(r'^supervisor/', include('sadiki.supervisor.urls')),
    url(r'^logs/', include('sadiki.logger.urls')),
    url(r'^statistics/', include('sadiki.statistics.urls')),
    url(r'^', include('sadiki.core.urls')),
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt',
                                              content_type='text/plain')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^vk/', VkontakteFrame.as_view(), name='vk_app'),
    url(r'^admin/', include(admin.site.urls)),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': settings.MEDIA_ROOT}),
    ]


for plugin in plugins:
    if isinstance(plugin, SadikiPlugin):
        try:
            urlpatterns += plugin.get_urls()
        except NotImplementedError:
            pass
