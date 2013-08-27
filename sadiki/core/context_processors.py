# -*- coding: utf-8 -*-
from sadiki.core import models as core_models
from sadiki.core.models import Preference, PREFERENCE_SECTION_MUNICIPALITY, PREFERENCE_MUNICIPALITY_PHONE, \
    PREFERENCE_MUNICIPALITY_NAME_GENITIVE


def constants(request):
    u"""
    Нам нужны все варианты для полей с атрибутом choice,
    например статусы заявки
    В шаблон передаются все объекты типа int из файла моделей модуля core
    """
    all_members = dir(core_models)
    int_constants = filter(lambda a: type(getattr(core_models, a)) is int, all_members)

    return dict((attr_name, getattr(core_models, attr_name)) for attr_name in int_constants)


def municipality_settings(request):
    u"""Все элементы конфигурационного файла из раздела municipality передаются в шаблон"""
    try:
        MUNICIPALITY_NAME_GENITIVE = Preference.objects.get(section=PREFERENCE_SECTION_MUNICIPALITY,
            key=PREFERENCE_MUNICIPALITY_NAME_GENITIVE)
    except Preference.DoesNotExist:
        MUNICIPALITY_NAME_GENITIVE = None
    try:
        MUNICIPALITY_PHONE = Preference.objects.get(section=PREFERENCE_SECTION_MUNICIPALITY,
            key=PREFERENCE_MUNICIPALITY_PHONE)
    except Preference.DoesNotExist:
        MUNICIPALITY_PHONE = None
    return {'MUNICIPALITY_NAME_GENITIVE': MUNICIPALITY_NAME_GENITIVE, 'MUNICIPALITY_PHONE': MUNICIPALITY_PHONE}
