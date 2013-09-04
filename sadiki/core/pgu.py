# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import transaction
from sadiki.core.models import EvidienceDocument, Profile, STATUS_REQUESTER, REQUESTION_TYPE_GOSUSLUGI, Requestion
from sadiki.core.utils import get_unique_username
from django.utils.translation import activate
import re
import datetime
from sadiki.core import workflow
from sadiki.core.workflow import SET_REQUESTION_LOCATION_BY_PGU
from sadiki.logger.models import Logger


# используем прокси модели, для изменения названия полей, т.к. эти названия будут
# отображаться в сообщениях об ошибках

class ProfilePGU(Profile):
    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        self._meta.get_field('pgu_email').verbose_name = u'Адрес электронной почты'
        self._meta.get_field('pgu_mobile_phone').verbose_name = u'Мобильный телефон'
        super(ProfilePGU, self).__init__(*args, **kwargs)

profile_fields = ["pgu_email", "pgu_mobile_phone"]


class RequestionPGU(Requestion):

    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        self._meta.get_field('name').verbose_name = u'Имя ребенка'
        self._meta.get_field('birth_date').verbose_name = u'Дата рождения ребенка'
        self._meta.get_field('location_properties').verbose_name = u'Адрес'
        super(RequestionPGU, self).__init__(*args, **kwargs)


requestion_fields = ["name", "birth_date", "location_properties", "admission_date"]


def errors_dict_to_list(instance, errors_dict):
    errors = []
    for field_name, field_errors in errors_dict.iteritems():
        if field_name != "__all__":
            errors.append(u"{0}: {1}".format(instance._meta.get_field(field_name).verbose_name, u" ".join(field_errors)))
    return errors


def create_profile_and_requestion(email, mobile_phone, name, birth_date, document_template,
                                  document_series, document_number,
                                  town, street, building_number, block_number, flat_number,
                                  preferred_sadiks, admission_year):
    u"""
    Регистрация заявки в системе. Возвращается словарь, содержащий статус(status)
    Возможные значения статуса:
        already_registered - заявка уже зарегистрирована, также возвращается номер заявка(requestion)
        validation_error - ошибки во входных данных, также возвращается список ошибок(errors)
        registration_complete - успешная регистрация, также возвращается имя пользователя(username), пароль(password)
            и заявка(requestion)

    Аргументы:
    email - электронная почта
    mobile_phone - номер телефона(строка)
    name - имя ребенка
    birth_date - дата рождения ребенка
    document_template - тип документа(объект типа EvidienceDocumentTemplate)
    document_series - серия документа(строка)
    document_number - номер документа(строка)
    town - город(строка)
    street - улица(строка)
    building_number - номер дома(строка или число)
    block_number - корпус
    flat_number - квартира(не используется)
    preferred_sadiks - список приоритетных ДОУ(объекты типа Sadik)
    admission_year - желаемый год зачисления(число)
    """
    # мы хотим получать русские сообщения об ошибках
    activate('ru')
    location_properties = ' '.join([town, street, unicode(building_number), unicode(block_number)])
    document_number = " ".join((document_series, unicode(document_number)))
    admission_date = datetime.date(admission_year, 01, 01)
    errors = []
    # проверяем, что номер документа совпадает с шаблоном
    if document_number and document_template and not re.match(
        document_template.regex, document_number):
        errors.append(u'Номер документа не совпадает с форматом')
    else:
        try:
            document = EvidienceDocument.objects.get(document_number=document_number,
                confirmed=True, template=document_template)
        except EvidienceDocument.DoesNotExist:
            pass
        else:
            requestion = document.content_object
            #если такой документ уже задан и подтвержден
            return {"status": "already_registered", "requestion": requestion}
    # проверяем профиль
    profile = ProfilePGU(pgu_email=email, pgu_mobile_phone=mobile_phone)
    profile_fields_names = ProfilePGU._meta.get_all_field_names()
    exclude_profile_fields_names = [field_name for field_name in profile_fields_names
                                    if field_name not in profile_fields]
    try:
        profile.full_clean(exclude=exclude_profile_fields_names)
    except ValidationError as e:
        profile_errors = e.message_dict
        errors.extend(errors_dict_to_list(profile, profile_errors))
    # проверяем заявку
    requestion = RequestionPGU(name=name, birth_date=birth_date, distribute_in_any_sadik=True,
                               status=STATUS_REQUESTER, cast=REQUESTION_TYPE_GOSUSLUGI,
                               location_properties=location_properties, admission_date=admission_date)
    requestion_fields_names = RequestionPGU._meta.get_all_field_names()
    exclude_requestions_fields_names = [field_name for field_name in requestion_fields_names
                                    if field_name not in requestion_fields]
    try:
        requestion.full_clean(exclude=exclude_requestions_fields_names)
    except ValidationError as e:
        requestion_errors = e.message_dict
        errors.extend(errors_dict_to_list(requestion, requestion_errors))
    if not errors:
        # ошибок нет, производим запись в БД
        with transaction.commit_on_success():
            user = User(username=get_unique_username())
            password = User.objects.make_random_password()
            user.set_password(password)
            user.save()
            #задаем имя пользователя на основании id в БД
            user.set_username_by_id()
            user.save()
            #        задаем права
            permission = Permission.objects.get(codename=u'is_requester')
            user.user_permissions.add(permission)
            profile.user = user
            profile.save()
            requestion.profile = profile
            requestion.save()
            requestion.pref_sadiks = preferred_sadiks
            #создаем документ
            document = EvidienceDocument.objects.create(
                template=document_template,
                document_number=document_number,
                object_id=requestion.id,
                content_type=ContentType.objects.get_for_model(requestion),
                confirmed=True,)
            Logger.objects.create_for_action(
                workflow.REQUESTION_REGISTRATION_BY_PGU,
                context_dict={"requestion": requestion, "pref_sadiks": preferred_sadiks},
                extra={"obj": requestion, 'added_pref_sadiks': preferred_sadiks})
            return {"status": "registration_complete", "username": user.username, "password": password,
                "requestion": requestion}
    else:
        return {"status": "validation_error", "errors": errors}


def change_user_password(user, new_password):
    u"""
    задает новый пароль для пользователя

    user - объект типа User
    new_password - пароль в виде текста
    """
    user.set_password(new_password)
    user.save()


def change_requestion_location(requestion, latitude, longtitude):
    u"""
    устанавливает координаты для заявки

    requestion - объект типа Requestion
    latitude - широта(число)
    longtitude - долгота(число)
    """

    requestion.location = Point(longtitude, latitude)
    requestion.location_properties = None
    Logger.objects.create_for_action(
        SET_REQUESTION_LOCATION_BY_PGU,
        context_dict={"requestion": requestion},
            extra={"obj": requestion})
    requestion.save()