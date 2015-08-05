# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from pysnippets import dttools
from sadiki.core.models import Requestion, REQUESTION_IDENTITY, \
    EvidienceDocument


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
            'middle_name': requestion.child_middle_name,
            'last_name': requestion.child_last_name,
            'parent_first_name': requestion.profile.first_name,
            'parent_middle_name': requestion.profile.middle_name,
            'parent_last_name': requestion.profile.last_name,
            'phone': requestion.profile.phone_number or requestion.profile.mobile_number,
            'sex': requestion.sex,
            'status': requestion.status,
            'queue_profile_url': url,
            'birth_date': dttools.date_to_stamp(requestion.birth_date),
            'birth_cert': birth_cert.document_number})
        req_list.append(requestion_data)

    return req_list


def is_active_child_status(status):
    u"""
    Проверяем числится ребенок активным в ЭС, или же выпущен
    """
    return status not in [3, 4, 5, 8, 9]
