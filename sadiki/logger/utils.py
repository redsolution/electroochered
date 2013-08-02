# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from ordereddict import OrderedDict
from sadiki.conf_settings import SPECIAL_TRANSITIONS
from sadiki.core.models import Requestion
from sadiki.logger.models import Logger


def add_special_transitions_to_requestions(requestions):
    requestions_dict = OrderedDict([(requestion.id, requestion) for requestion in requestions])
    requestions_ids = [requestion.id for requestion in requestions]
    logs = Logger.objects.filter(content_type=ContentType.objects.get_for_model(Requestion),
        object_id__in=requestions_ids, action_flag__in=SPECIAL_TRANSITIONS)
    relation_dict = {}
    for log in logs:
        requestion_log = relation_dict.get(log.object_id)
#            если для данной заявки не задан лог или он более старый
        if not requestion_log or requestion_log.datetime < log.datetime:
            relation_dict[log.object_id] = log
    for id, log in relation_dict.items():
        requestions_dict[id].action_log = log
    return requestions