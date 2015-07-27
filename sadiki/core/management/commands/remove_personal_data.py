# -*- coding: utf-8 -*-
import logging
import datetime
import random
import string
import sys

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db.utils import IntegrityError
from sadiki.core.models import Benefit, Profile, Requestion, PersonalDocument
from sadiki.logger.models import Logger, LoggerMessage


def generate_random_date(start, end):
    delta = end - start
    return start + datetime.timedelta(random.randrange(delta.days))

def generate_random_snils():
    return '{}-{}-{} {}'.format(
        random.randint(100, 999),
        random.randint(100, 999),
        random.randint(100, 999),
        random.randint(10, 99))

def generate_random_phone_number():
    return '+7({}){}'.format(
        random.randint(900, 999),
        ''.join([random.choice(string.digits) for _ in range(7)]))


class Command(BaseCommand):
    help_text = '''Usage: manage.py remove_personal_data'''

    def handle(self, *args, **options):
        print u"Изменяем описание льгот"
        benefits = Benefit.objects.all()
        for benefit in benefits:
            benefit.name = u"Льгота №{} категории {}".format(
                benefit.id, benefit.category.id)
            benefit.description = benefit.name
            benefit.save()

        print u"Удаляем содержимое логов"
        from sadiki.core.workflow import ANONYM_LOG
        LoggerMessage.objects.filter(level__gt=ANONYM_LOG).update(message=u"")

        sex_data = [u'М', u'Ж']

        men_data = {
            'first_names': ['Вася', 'Федя', 'Коля', 'Степан', 'Алексей',
                            'Дмитрий', 'Егор', 'Владимир', 'Влад', 'Александр',
                            'Виталий', 'Иван', 'Евгений', 'Игорь', 'Андрей'],
            'middle_names': ['Васильевич', 'Федорович', 'Николаевич',
                             'Степанович', 'Алексеевич', 'Дмитриевич',
                             'Егорович', 'Владимирович', 'Владиславович',
                             'Александрович', 'Витальевич', 'Иванович',
                             'Евгеньевич', 'Игоревич', 'Андреевич'],
            'last_names': ['Иванов', 'Сидоров', 'Петров', 'Буйко', 'Савельев',
                           'Ищенко', 'Брут', 'Боровик', 'Весельев', 'Дворский',
                           'Симонов', 'Леантович', 'Саломатов', 'Козочкин']
        }
        women_data = {
            'first_names': ['Аня', 'Ирина', 'Маша', 'Света', 'Алена',
                            'Ангелина', 'Катя', 'Вера', 'Влада', 'Надежда',
                            'Василиса', 'Вика', 'Евгения', 'Юлия', 'Алефтина'],
            'middle_names': ['Васильевна', 'Федоровна', 'Николаевна',
                             'Степановна', 'Алексеевна', 'Дмитриевна',
                             'Егоровна', 'Владимировна', 'Владиславовна',
                             'Александровна', 'Витальевна', 'Ивановна',
                             'Евгеньевна', 'Игоревна', 'Андреевна'],
            'last_names': ['Иванова', 'Сидорова', 'Петрова', 'Буйко', 'Ищенко',
                           'Савельева', 'Брут', 'Боровик', 'Весельева',
                           'Дворская', 'Симонова', 'Леантович', 'Саломатова',
                           'Козочкина']
        }
        name_data = {u"М": men_data, u"Ж": women_data}

        address_data = {
            'town': ['Нью-Йорк', 'Лондон', 'Москва', 'деревня Гадюкино',
                           'Париж', 'Оттава', 'Рим', 'Прага', 'Каир'],
            'street': ['Веселая', 'Тенистая', '5-я Авеню', 'Улиточная',
                       'генерала Уранова', 'Светлая', 'Ленина', 'Пушкина'],
        }

        kinship_data = [u'Мать', u'Отец', u'Опекун']


        print u"Изменяем персональные данные детей"
        all_requestions = Requestion.objects.all()
        for requestion in all_requestions:
            requestion.sex = random.choice(sex_data)
            requestion.name = random.choice(
                name_data[requestion.sex]['first_names'])
            requestion.child_last_name = random.choice(
                name_data[requestion.sex]['last_names'])
            requestion.child_middle_name = random.choice(
                name_data[requestion.sex]['middle_names'])
            requestion.birthplace = random.choice(address_data['town'])
            requestion.child_snils = generate_random_snils()
            requestion.kinship = random.choice(kinship_data)
            requestion.save()

        print u"Изменяем персональные данные пользователей"
        all_profiles = Profile.objects.all()
        for profile in all_profiles:
            sex = random.choice(sex_data)
            profile.first_name = random.choice(name_data[sex]['first_names'])
            profile.middle_name = random.choice(name_data[sex]['middle_names'])
            profile.last_name = random.choice(name_data[sex]['last_names'])
            profile.town = random.choice(address_data['town'])
            profile.street = random.choice(address_data['street'])
            profile.house = str(random.randint(1, 99))
            profile.phone_number = generate_random_phone_number()
            profile.mobile_number = generate_random_phone_number()
            profile.snils = generate_random_snils()
            profile.save()
            documents = profile.personaldocument_set.all()
            for document in documents:
                doc_data_is_unique = False
                while not doc_data_is_unique:
                    series = ''.join([
                        random.choice(string.digits) for _ in range(4)])
                    number = ''.join([
                        random.choice(string.digits) for _ in range(6)])
                    doc_data_is_unique = not PersonalDocument.objects.filter(
                        doc_type=document.doc_type,
                        series=series, number=number
                    ).exists()
                document.series = series
                document.number = number
                document.issued_date = generate_random_date(
                    datetime.date(2010, 1, 1), datetime.date.today())
                document.issued_by = 'organization {}'.format(
                    random.randint(1, 100))
                document.save()

        print u"Удаляем почту"
        User.objects.all().update(email='')
