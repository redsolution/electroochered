# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf import settings
from django.contrib.gis.admin.options import OSMGeoAdmin
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import Point
from sadiki.administrator.models import ImportTask
from sadiki.core.models import Profile, Requestion, Sadik, Address, \
    EvidienceDocument, EvidienceDocumentTemplate, Distribution, Area


# Преобразование координат в x/y
transform = CoordTransform(SpatialReference(4326), SpatialReference(900913))
point = Point(
    float(settings.MAP_CENTER.split(',')[0]),
    float(settings.MAP_CENTER.split(',')[1]),
    srid=4326)
point.transform(transform)

class CustomGeoAdmin(OSMGeoAdmin):

    openlayers_url = settings.STATIC_URL + 'openlayers/OpenLayers.js'
    extra_js = [settings.STATIC_URL + 'js/libs/OpenStreetMap.js',
                settings.STATIC_URL + 'js/openlayers_style_change.js']
    default_lat = point.y
    default_lon = point.x
    default_zoom = settings.MAP_ZOOM


class AreaAdmin(CustomGeoAdmin):
    pass

class RequestionAdmin(admin.ModelAdmin):
    list_display = ('requestion_number', 'number_in_old_list', 'last_name',
        'first_name', 'patronymic')
    search_fields = ('profile__user__username', 'number_in_old_list')
    raw_id_fields = ('profile', )


class SadikAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class ProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)
    raw_id_fields = ('user',)

class AddressAdmin(CustomGeoAdmin):
    search_fields = ('street', 'postindex')
    list_display = ('__unicode__', 'has_coords')

    def has_coords(self, obj):
        return bool(obj.coords)
    has_coords.short_description = u'Коодинаты'
    has_coords.boolean = True

admin.site.register(Distribution, admin.ModelAdmin)
admin.site.register(EvidienceDocument, admin.ModelAdmin)
admin.site.register(EvidienceDocumentTemplate, admin.ModelAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Requestion, RequestionAdmin)
admin.site.register(Sadik, SadikAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(ImportTask)
