# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.core import management
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import Client
from django.test.testcases import TestCase
import unittest
from sadiki.core.models import Requestion, Profile, STATUS_REQUESTER, Address, \
    Area, Sadik, REQUESTION_IDENTITY, AgeGroup, SadikGroup, STATUS_DECISION, \
    Preference, PREFERENCE_IMPORT_FINISHED, STATUS_SHORT_STAY, \
    STATUS_ON_DISTRIBUTION, Distribution, DISTRIBUTION_STATUS_INITIAL, \
    DISTRIBUTION_STATUS_ENDING
from sadiki.core.permissions import OPERATOR_GROUP_NAME, \
    SADIK_OPERATOR_GROUP_NAME, DISTRIBUTOR_GROUP_NAME, SUPERVISOR_GROUP_NAME
from sadiki.core.utils import get_current_distribution_year
from sadiki.distribution.views import DecisionManager
import datetime
import random


class TestAll(TestCase):
    fixtures = [
        'sadiki/core/fixtures/test_initial.json',
        'sadiki/core/fixtures/perms.json',
        'sadiki/core/fixtures/groups.json',
        ]

    def setUp(self):
        address = Address.objects.create(postindex=123456, street=u'ул.Кирова',
                                         building_number=17, )
        # Area.objects.create(name='test', ocato='123456')  # , address=address)
        #        Requestion.objects.all().update(status=STATUS_REQUESTER)
        self.operator = User(username='operator')
        self.operator.set_password("password")
        self.operator.save()
        Profile.objects.create(user=self.operator)
        operator_group = Group.objects.get(name=OPERATOR_GROUP_NAME)
        sadik_operator_group = Group.objects.get(name=SADIK_OPERATOR_GROUP_NAME)
        distributor_group = Group.objects.get(name=DISTRIBUTOR_GROUP_NAME)
        self.operator.groups = (
            operator_group, sadik_operator_group, distributor_group)
        self.supervisor = User(username="supervisor")
        self.supervisor.set_password("password")
        self.supervisor.save()
        Profile.objects.create(user=self.supervisor)
        supervisor_group = Group.objects.get(name=SUPERVISOR_GROUP_NAME)
        self.supervisor.groups = (supervisor_group,)

    def test_distribution(self):
        management.call_command('generate_sadiks', 10)
        management.call_command('generate_requestions', 200,
                                distribute_in_any_sadik=True)
        Requestion.objects.all().update(status=STATUS_REQUESTER)
        # Requestion.objects.all().update(cast=3)
        current_datetime = datetime.date.today()
        current_distribution_year = get_current_distribution_year()
        for age_group in AgeGroup.objects.all():
            group_min_birth_date = age_group.min_birth_date()
            group_max_birth_date = age_group.max_birth_date()
            for sadik in Sadik.objects.all():
                SadikGroup.objects.create(
                    free_places=10,
                    capacity=10, age_group=age_group, sadik=sadik,
                    year=current_distribution_year,
                    min_birth_date=group_min_birth_date,
                    max_birth_date=group_max_birth_date)
        # группа заявок с датой распределения преывшающей текущую
        # они не должны быть распределены
        requestions_admission_date_ids = list(Requestion.objects.all(
        ).order_by('?')[:30].values_list('id', flat=True))
        try:
            admission_date = current_datetime.replace(
                year=current_datetime.year + 1)
        except ValueError:
            admission_date = current_datetime.replace(
                year=current_datetime.year + 1, day=current_datetime.day - 1)
        Requestion.objects.filter(
            id__in=requestions_admission_date_ids
        ).update(admission_date=admission_date)
        # добавим новые ДОУ без мест и заявки желающие распределиться только
        # в эти ДОУ
        existing_sadiks_ids = list(Sadik.objects.all().values_list(
            'id', flat=True))
        management.call_command('generate_sadiks', 5)
        new_sadiks = list(Sadik.objects.exclude(id__in=existing_sadiks_ids))
        # TODO: Исправить тест, с учетом distribute_in_any_sadik = True!!!
        requestions_pref_sadiks_ids = list(Requestion.objects.exclude(
            id__in=requestions_admission_date_ids
        ).order_by('?')[:30].values_list('id', flat=True))
        for requestion in Requestion.objects.filter(
                id__in=requestions_pref_sadiks_ids):
            requestion.pref_sadiks = new_sadiks
            requestion.distribute_in_any_sadik = True
            requestion.save()
        requestions_area_distribution_ids = list(Requestion.objects.exclude(
            id__in=requestions_admission_date_ids + requestions_pref_sadiks_ids
        )[:30].values_list('id', flat=True))
        Requestion.objects.filter(id__in=requestions_area_distribution_ids
        ).update(distribute_in_any_sadik=True)
        for requestion in Requestion.objects.filter(
                id__in=requestions_area_distribution_ids):
            requestion.areas = (random.choice(Area.objects.all()),)
            requestion.pref_sadiks = []
        client = Client()
        client.login(username=self.operator.username, password="password")
        client.post(reverse('distribution_init'), data={'confirmation': 'yes'},
                    follow=True)
        decision_manager = DecisionManager()
        last_distributed_requestion = None
        queue_info = decision_manager.queue_info()
        total = 0
        while queue_info['free_places'] and queue_info['queue']:
            requestion = queue_info['current_requestion']
            if last_distributed_requestion:
                self.assertEqual(last_distributed_requestion,
                                 queue_info['last_distributed_requestion'], )
            sadiks_for_requestion_dict = decision_manager.sadiks_for_requestion(
                requestion)
            sadiks_for_requestion = \
                sadiks_for_requestion_dict['pref_sadiks'] or \
                sadiks_for_requestion_dict['any_sadiks']
            sadik = sadiks_for_requestion[0]
            if requestion.cast == 1:
                response = client.post(
                    reverse('decision_manager'),
                    data={
                        'sadik': sadik.id,
                        'requestion_id': requestion.id,
                        'accept_location': True}
                )
            else:
                response = client.post(
                    reverse('decision_manager'),
                    data={'sadik': sadik.id, 'requestion_id': requestion.id})
            if response.status_code == 302:
                last_distributed_requestion = requestion
                total += 1
            queue_info = decision_manager.queue_info()

        # проверяем,что заявки с ЖДП, превышающим текущую дату и желающие
        # зачислиться в ДОУ без мест не распределены
        # закомментировал с учетом distribute_in_any_sadik = True
        requestions_not_decision_ids = list(requestions_admission_date_ids)
        # + list(requestions_pref_sadiks_ids)

        self.assertEqual(
            Requestion.objects.filter(
                id__in=requestions_not_decision_ids).filter(
                status=STATUS_DECISION).count(), 0)

        # проверяем, что заявка была зачислена в свою возрастную группу
        for requestion in Requestion.objects.filter(status=STATUS_DECISION):
            self.assertIn(
                requestion.distributed_in_vacancy.sadik_group.age_group,
                requestion.age_groups())

        # проверяем, что заявки, которые указали возможность зачисления в
        # любой ДОУ были зачислены в нужную территориальную область
        for requestion in Requestion.objects.filter(
                id__in=requestions_area_distribution_ids,
                distributed_in_vacancy__isnull=False):
            # проверяем, что заявка попадает в какую-нибудь возрастную группу и
            # может быть распределена
            if requestion.age_groups():
                self.assertEqual(
                    requestion.areas.all()[0],
                    requestion.distributed_in_vacancy.sadik_group.sadik.area)

    def test_previous_status_return_after_distribution(self):
        management.call_command('generate_requestions', 10,
                                distribute_in_any_sadik=True)
        Requestion.objects.all().update(status=STATUS_REQUESTER)
        requestions = Requestion.objects.all()
        self.assertEqual(10, len(requestions))

        # подготавливаем начальный набор данных
        # 5 зявок "Посещает группу кратковременного пребывания"
        requestions_short_stay = requestions[:5]
        self.assertEqual(5, len(requestions_short_stay))
        for requestion in requestions_short_stay:
            requestion.status = STATUS_SHORT_STAY
            requestion.save()
            self.assertEqual(requestion.status, STATUS_SHORT_STAY)
            self.assertIsNone(requestion.previous_status)

        # 5 зявок "Очередник"
        requestions_requester = requestions[5:]
        self.assertEqual(5, len(requestions_requester))
        for requestion in requestions_requester:
            self.assertEqual(requestion.status, STATUS_REQUESTER)
            self.assertIsNone(requestion.previous_status)

        # открываем распределение
        login = self.client.login(
            username=self.operator.username, password="password")
        self.assertTrue(login)
        dist_response = self.client.post(reverse('distribution_init'), data={
            'confirmation': 'yes'}, follow=True)
        self.assertEqual(dist_response.status_code, 200)

        # все заявки должны перейти в статус "На комплектовании"
        # предыдущий статус хранится в атрибуте previous_status
        for requestion in requestions_requester:
            requestion = Requestion.objects.get(pk=requestion.pk)
            self.assertEqual(requestion.status, STATUS_ON_DISTRIBUTION)
            self.assertEqual(requestion.previous_status, STATUS_REQUESTER)

        for requestion in requestions_short_stay:
            requestion = Requestion.objects.get(pk=requestion.pk)
            self.assertEqual(requestion.status, STATUS_ON_DISTRIBUTION)
            self.assertEqual(requestion.previous_status, STATUS_SHORT_STAY)

        # завершаем распределение
        start_distribution = Distribution.objects.get(
            status=DISTRIBUTION_STATUS_INITIAL)
        start_distribution.status = DISTRIBUTION_STATUS_ENDING
        start_distribution.to_datetime = datetime.datetime.now()
        start_distribution.save()
        management.call_command('end_distribution', self.operator.username)
        self.assertEqual(0, len(Requestion.objects.filter(
            status=STATUS_ON_DISTRIBUTION)))

        # все заявки должны перейти в статус, который имели до распределения
        # предыдущий статус не меняем для повышения быстродействия операции
        for requestion in requestions_requester:
            requestion = Requestion.objects.get(pk=requestion.pk)
            self.assertEqual(requestion.status, STATUS_REQUESTER)

        for requestion in requestions_short_stay:
            requestion = Requestion.objects.get(pk=requestion.pk)
            self.assertEqual(requestion.status, STATUS_SHORT_STAY)

