# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from pysnippets import dttools
from django.conf import settings
from sadiki.core.models import Requestion, REQUESTION_IDENTITY, \
    EvidienceDocument

USE_PDATA = 'personal_data' in settings.INSTALLED_APPS
if USE_PDATA:
    try:
        from personal_data.models import ChildPersData, UserPersData
    except ImportError:
        USE_PDATA = False


def add_requestions_data(requestions, request):
    u""" Requestion, HttpRequest -> List of Dict

    Функция для сбора информации о заявках для дальнейшей конвертации в json.
    Используется в API вызовах для экспорта зачисленных заявок в ЭС.
    Возвращает список словарей.
    """
    requestion_ct = ContentType.objects.get_for_model(Requestion)
    req_list = []
    for requestion in requestions:
        birth_cert = EvidienceDocument.objects.filter(
            template__destination=REQUESTION_IDENTITY,
            content_type=requestion_ct, object_id=requestion.id)[0]
        url = request.build_absolute_uri(reverse(
            'requestion_logs', args=(requestion.id, )))
        requestion_data = ({
            'requestion_number': requestion.requestion_number,
            'requestion_id': requestion.id,
            'distribution_datetime': dttools.datetime_to_stamp(
                requestion.status_change_datetime),
            'name': requestion.name,
            'sex': requestion.sex,
            'status': requestion.status,
            'queue_profile_url': url,
            'birth_date': dttools.date_to_stamp(requestion.birth_date),
            'birth_cert': birth_cert.document_number})
        if USE_PDATA:
            requestion_data.update(get_personal_data(requestion))
        req_list.append(requestion_data)

    return req_list


def get_personal_data(requestion):
    u""" Requestion -> Dict
    Собираем персональные данные о заявке персональные данные, при наличии.
    Возвращаем словарь.
    """
    pdata = {}
    if ChildPersData.objects.filter(application=requestion).exists():
        child_pdata = ChildPersData.objects.get(application=requestion)
        pdata.update({
            'middle_name': child_pdata.second_name,
            'last_name': child_pdata.last_name,
        })
    if UserPersData.objects.filter(profile=requestion.profile).exists():
        user_pdata = UserPersData.objects.get(profile=requestion.profile)
        pdata.update({
            'parent_first_name': user_pdata.first_name,
            'parent_middle_name': user_pdata.second_name,
            'parent_last_name': user_pdata.last_name,
            'phone': user_pdata.phone,
        })
    return pdata


def is_active_child_status(status):
    u"""
    Проверяем числится ребенок активным в ЭС, или же выпущен
    """
    return status not in [3, 4, 5, 8, 9]
