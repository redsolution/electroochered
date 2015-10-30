# -*- coding: utf-8 -*-
import json
import random
import hashlib

from rest_framework import serializers
from django.conf import settings
from django.core.serializers.python import Serializer as PythonSerializer
from django.core.serializers.json import DjangoJSONEncoder, Deserializer

from sadiki.core.models import Requestion, Sadik, AgeGroup, SadikGroup
from sadiki.core.management.commands.remove_personal_data import (
    generate_random_date, generate_random_snils, generate_random_phone_number,
    sex_data, men_data, women_data, name_data, address_data, kinship_data,
    earliest_issue_date, today
)
from sadiki.core.workflow import ANONYM_LOG
from sadiki.core.utils import get_fixture_chunk_file_name as get_chunk_filename


class LocationField(serializers.Field):
    def to_representation(self, value):
        return list(value)


class RequestionGeoSerializer(serializers.ModelSerializer):
    location = LocationField(source='location.tuple')

    class Meta:
        model = Requestion
        fields = ('id', 'requestion_number', 'location')


class AnonymRequestionGeoSerializer(serializers.ModelSerializer):
    location = LocationField(source='location.tuple')

    class Meta:
        model = Requestion
        fields = ('location', )


class AgeGroupSerializer(serializers.ModelSerializer):
    max_birth_date = serializers.DateField(format='%d.%m.%Y')
    min_birth_date = serializers.DateField(format='%d.%m.%Y')

    class Meta:
        model = AgeGroup
        fields = ('id', 'name', 'short_name', 'max_birth_date',
                  'min_birth_date')
        read_only_fields = ('id', 'name', 'short_name')


class SadikGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SadikGroup
        fields = ('id', 'age_group', 'capacity', 'free_places', 'active')


class SadikSerializer(serializers.ModelSerializer):
    groups = SadikGroupSerializer(read_only=True, required=False, many=True)
    # groups = serializers.SerializerMethodField('active_groups')

    class Meta:
        model = Sadik
        fields = ('id', 'short_name', 'age_groups',
                  'active_registration', 'active_distribution', 'groups')
        read_only_fields = (
            'id', 'short_name', 'age_groups', 'active_registration',
            'active_distribution')

    def active_groups(self, obj):
        groups_qs = obj.groups.active()
        return SadikGroupSerializer(groups_qs, many=True).data


# генерируем специальный секретный пароль для всех учетных записей
default_hash = hashlib.sha1('salt1' + '1234').hexdigest()
default_user_password = "{}${}${}".format('sha1', 'salt1', default_hash)


def remove_log_message(log):
    if log.level > ANONYM_LOG:
        return ''
    return log.message


def remove_benefit_name(benefit):
    return u"Льгота №{} категории {}".format(benefit.id, benefit.category.id)


def randomize_requestion_name(requestion):
    sex = requestion.sex or sex_data[requestion.id & 1]
    return random.choice(name_data[sex]['first_names'])


def randomize_requestion_child_last_name(requestion):
    sex = requestion.sex or sex_data[requestion.id & 1]
    return random.choice(name_data[sex]['last_names'])


def randomize_requestion_child_middle_name(requestion):
    sex = requestion.sex or sex_data[requestion.id & 1]
    return random.choice(name_data[sex]['middle_names'])


def randomize_requestion_kinship(requestion):
    if random.randint(0, 3) == 0:
        return u'Опекун'
    sex = sex_data[requestion.profile.user.id & 1]
    return u'Отец' if sex == u'М' else u'Мать'


def randomize_user_first_name(profile):
    sex = sex_data[profile.id & 1]
    return random.choice(name_data[sex]['first_names'])


def randomize_user_last_name(profile):
    sex = sex_data[profile.id & 1]
    return random.choice(name_data[sex]['last_names'])


def randomize_profile_middle_name(profile):
    sex = sex_data[profile.user.id & 1]
    return random.choice(name_data[sex]['middle_names'])


def remove_document_number(document):
    return str(100000 + document.id % 900000)


def remove_vk_uid(user_social_auth):
    u""" Ссылка на VK будет заведомо нерабочей, например vk.com/id_dummy_111"""
    return '_dummy_{}'.format(user_social_auth.id)


# функции для обезличивания персональных данных
# данные, для обезличивания которых не нужна доп. информация об объекте
FIELD_SIMPLE_DEPERSONALIZERS = {
    'User.email': lambda: '',
    'User.password': lambda: default_user_password,
    'Profile.town': lambda: random.choice(address_data['town']),
    'Profile.street': lambda: random.choice(address_data['street']),
    'Profile.house': lambda: str(random.randint(1, 99)),
    'Profile.phone_number': generate_random_phone_number,
    'Profile.mobile_number': generate_random_phone_number,
    'Profile.snils': generate_random_snils,
    'PersonalDocument.doc_name': lambda: u'Иной документ',
    'PersonalDocument.series': lambda: str(random.randint(1000, 9999)),
    'PersonalDocument.issued_date': lambda: generate_random_date(
        earliest_issue_date, today),
    'PersonalDocument.issued_by': lambda: u'Организация № {}'.format(
        random.randint(1, 100)),
    'Requestion.birthplace': lambda: random.choice(address_data['town']),
    'Requestion.child_snils': generate_random_snils,
}

# данные, для обезличивания которых нужно знать какую-либо доп. информацию
# например, Ф.И.О ребёнка должны соответствовать его полу
# а степень родства - полу родителя
FIELD_SPECIAL_DEPERSONALIZERS = {
    'LoggerMessage.message': remove_log_message,
    'Benefit.name': remove_benefit_name,
    'Benefit.description': remove_benefit_name,
    'Requestion.name': randomize_requestion_name,
    'Requestion.child_last_name': randomize_requestion_child_last_name,
    'Requestion.child_middle_name': randomize_requestion_child_middle_name,
    'Requestion.kinship': randomize_requestion_kinship,
    'User.first_name': randomize_user_first_name,
    'User.last_name': randomize_user_last_name,
    'Profile.middle_name': randomize_profile_middle_name,
    'PersonalDocument.number': remove_document_number,
    'UserSocialAuth.uid': remove_vk_uid,
}


class Serializer(PythonSerializer):
    u"""
    Отдельный сериалайзер для команды dumpdata для обезличивания
    персональных данных в момент создания дампа.
    Для использования в настройках необходимо добавить пункт:
        SERIALIZATION_MODULES = {'djson': 'sadiki.core.serializers'}
    и запускать команду ./manage.py dumpdata --format djson > data.djson
    """
    internal_use_only = False

    def start_serialization(self):
        self._current = None
        self.objects = []
        self.objects_counter = 0
        # максимальное количество записей в одном djson-файле
        self.chunk_size = getattr(settings, 'DJSON_CHUNK_SIZE', 50000)
        self.current_chunk_number = 1
        self.chunk_mode = isinstance(self.stream, file)
        if self.chunk_mode:
            self.base_output_fname = self.stream.name

    def end_serialization(self):
        if self.objects:
            json.dump(self.objects, self.stream, cls=DjangoJSONEncoder,
                      **self.options)

    def end_object(self, obj):
        super(Serializer, self).end_object(obj)
        self.objects_counter += 1
        if self.objects_counter == self.chunk_size and self.chunk_mode:
            json.dump(self.objects, self.stream, cls=DjangoJSONEncoder,
                      **self.options)
            self.stream.close()
            self.stream = open(
                get_chunk_filename(self.base_output_fname,
                                   self.current_chunk_number),
                'w'
            )
            self.objects_counter = 0
            self.objects = []
            self.current_chunk_number += 1

    def handle_field(self, obj, field):
        value = field._get_val_from_obj(obj)
        # не трогаем поля с пустыми значениями
        if not value:
            return super(Serializer, self).handle_field(obj, field)
        full_field_name = '%s.%s' % (obj._meta.object_name, field.name)
        if full_field_name in FIELD_SIMPLE_DEPERSONALIZERS:
            value = FIELD_SIMPLE_DEPERSONALIZERS[full_field_name]()
            self._current[field.name] = value
        elif full_field_name in FIELD_SPECIAL_DEPERSONALIZERS:
            value = FIELD_SPECIAL_DEPERSONALIZERS[full_field_name](obj)
            self._current[field.name] = value
        else:
            super(Serializer, self).handle_field(obj, field)

    def getvalue(self):
        if callable(getattr(self.stream, 'getvalue', None)):
            return self.stream.getvalue()
