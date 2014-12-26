# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from pysnippets import dttools
from sadiki.core.models import Requestion, REQUESTION_IDENTITY, \
    EvidienceDocument


def add_requestions_data(requestions, request):
    """
    Функция для сбора информации о заявках для дальнейшей конвертации в json.
    Используется в API вызовах для экспорта зачисленных заявок в ЭС.
    """
    requestion_ct = ContentType.objects.get_for_model(Requestion)
    req_list = []
    for requestion in requestions:
        birth_cert = EvidienceDocument.objects.filter(
            template__destination=REQUESTION_IDENTITY,
            content_type=requestion_ct, object_id=requestion.id)[0]
        url = request.build_absolute_uri(reverse(
            'requestion_logs', args=(requestion.id, )))
        req_list.append({
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
    return req_list
