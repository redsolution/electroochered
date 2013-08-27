#-*- coding:utf-8 -*-
from django.contrib import admin
from sadiki.core.models import Address

map_widget = admin.site._registry[Address].get_map_widget(Address._meta.get_field_by_name('coords')[0])
location_errors = {'no_geom' : u"Не указана точка, определяющая местоположение",}