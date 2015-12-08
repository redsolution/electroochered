# -*- coding: utf-8 -*-
import sys
import json
import re
import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from pysnippets import gpgtools
from sadiki.logger.models import Logger
from sadiki.core.workflow import REQUESTION_TRANSFER
from sadiki.core.models import Requestion, Area, Profile, EvidienceDocument, \
    EvidienceDocumentTemplate, REQUESTION_IDENTITY
from sadiki.core import utils as core_utils


class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(sys.argv) > 2:
            for f in sys.argv[2:]:
                data = open(f, 'r').read()
                decrypted_data = gpgtools.decrypt_data(data)
                data = json.loads(str(decrypted_data))
                for item in data:
                    req = create_requestion(item)
                    print req
        else:
            data = sys.stdin.read()
            decrypted_data = gpgtools.decrypt_data(data)
            data = json.loads(str(decrypted_data))
            for item in data:
                req = create_requestion(item)
                print req


def create_document(requestion, document_number, document_type):

    BIRTH_DOC_SIMPLE = 0
    BIRTH_DOC_SIMPLE_TEMPLATE = EvidienceDocumentTemplate.objects.get(
        destination=REQUESTION_IDENTITY,
        regex=ur'^[A-Z]{1,3}-[А-Я]{1,2} \d{6,7}$')
    BIRTH_DOC_FOREIGN = 1
    BIRTH_DOC_FOREIGN_TEMPLATE = EvidienceDocumentTemplate.objects.filter(
        destination=REQUESTION_IDENTITY,
        regex=ur'.*')[0]
    if document_type == BIRTH_DOC_SIMPLE:
        template = BIRTH_DOC_SIMPLE_TEMPLATE
    else:
        template = BIRTH_DOC_FOREIGN_TEMPLATE
    document = EvidienceDocument(
        template=template,
        document_number=document_number,
        object_id=requestion.id,
        content_type=ContentType.objects.get_for_model(requestion)
    )
    document.save()
    return document


def create_profile():
    user = User.objects.create_user(username=core_utils.get_unique_username())
    permission = Permission.objects.get(codename=u'is_requester')
    user.user_permissions.add(permission)
    user.set_username_by_id()
    user.save()
    return Profile.objects.create(user=user)


def create_requestion(data, create_log=True):
    """
    Создаем заявку по предоставленной информации. Фомат data - словарь:
    {'name': Имя ребенка, без пробелов;
     'birth_date': дата рождения;
     'sex': пол (u"М" или u"Ж");
     'district': район проживания, если в системе активированы районы;
     'location_properties': адрес проживания прописью, свободная форма;
     'profile': профиль заявителя, создается автоматически;
     'registration_datetime': дата постановки в очередь (unixtimestamp);
     'birth_doc': номер свидетельства о рождении (unixtimestamp);
     'birth_doc_type': тип свидетельства о рождении, 0 - российский,
                       1 - зарубежное
    }

    :return:
    """
    # проверяем свидетельство о рождении
    BIRTH_DOC_SIMPLE = 0
    BIRTH_DOC_SIMPLE_TEMPLATE = EvidienceDocumentTemplate.objects.get(
        destination=REQUESTION_IDENTITY,
        regex=ur'^[A-Z]{1,3}-[А-Я]{1,2} \d{6,7}$')
    if not data.get('birth_doc'):
        return u"Не указан номер свидетельства о рождении"
    if data.get('birth_doc_type') == BIRTH_DOC_SIMPLE and not \
            (re.match(BIRTH_DOC_SIMPLE_TEMPLATE.regex,
                      data.get('birth_doc'))):
        return u"неверный формат свидетельства о рождении"
    try:
        EvidienceDocument.objects.get(document_number=data['birth_doc'],
                                      confirmed=True)
    except ObjectDoesNotExist:
        pass
    else:
        return u"Документ с таким номером уже занят"

    if not 'registration_datetime' in data.keys():
        return u"Не указана дата постановки в очередь"
    defaults = {
        'name': data.get('name'),
        'district': None,
        'sex': data.get('sex'),
        'location_properties': data.get('location_properties'),
        'profile': create_profile(),
        'birth_date': datetime.date.fromtimestamp(data.get('birth_date')),
        'registration_datetime': datetime.datetime.fromtimestamp(
            data.get('registration_datetime')),
    }
    try:
        req = Requestion.objects.create(**defaults)
    except Exception as e:
        return e.message
    req.areas.add(*[area for area in Area.objects.all()])
    create_document(req, data['birth_doc'], data['birth_doc_type'])
    # создаем запись в логах
    if create_log:
        Logger.objects.create_for_action(
            REQUESTION_TRANSFER,
            context_dict={'sender_info': data.get('sender_info'), },
            extra={'obj': req}
        )
    return req