# -*- coding: utf-8 -*-
import random
import datetime
from django.test import TestCase, Client
from django.core import management
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.db.models import Q

from sadiki.core.models import Profile, BenefitCategory, Requestion, Sadik, \
    SadikGroup, Preference, PREFERENCE_IMPORT_FINISHED, \
    Address, RequestionQuerySet, STATUS_NOT_APPEAR,  STATUS_REQUESTER, \
    STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REMOVE_REGISTRATION
from sadiki.core.permissions import OPERATOR_GROUP_NAME, \
    SUPERVISOR_GROUP_NAME, SADIK_OPERATOR_GROUP_NAME, DISTRIBUTOR_GROUP_NAME


OPERATOR_USERNAME = 'operator'
OPERATOR_PASSWORD = 'password'

SUPERVISOR_USERNAME = 'supervisor'
SUPERVISOR_PASSWORD = 'password'

REQUESTER_USERNAME = 'requester'
REQUESTER_PASSWORD = '1234'


class CoreViewsTest(TestCase):
    fixtures = ['sadiki/core/fixtures/test_initial.json', ]

    @classmethod
    def setUpClass(cls):
        management.call_command('update_initial_data')

    @classmethod
    def tearDownClass(cls):
        Permission.objects.all().delete()
        Group.objects.all().delete()
        BenefitCategory.objects.all().delete()
        Sadik.objects.all().delete()
        Address.objects.all().delete()

    def setUp(self):
        management.call_command('generate_sadiks', 1)
        management.call_command('generate_requestions', 25,
                                distribute_in_any_sadik=True)

        self.operator = User(username=OPERATOR_USERNAME)
        self.operator.set_password(OPERATOR_PASSWORD)
        self.operator.save()
        Profile.objects.create(user=self.operator)
        operator_group = Group.objects.get(name=OPERATOR_GROUP_NAME)
        sadik_operator_group = Group.objects.get(
            name=SADIK_OPERATOR_GROUP_NAME)
        distributor_group = Group.objects.get(name=DISTRIBUTOR_GROUP_NAME)
        self.operator.groups = (operator_group, sadik_operator_group,
                                distributor_group)
        self.supervisor = User(username=SUPERVISOR_USERNAME)
        self.supervisor.set_password(SUPERVISOR_PASSWORD)
        self.supervisor.save()
        Profile.objects.create(user=self.supervisor)
        supervisor_group = Group.objects.get(name=SUPERVISOR_GROUP_NAME)
        self.supervisor.groups = (supervisor_group,)

        self.requester = User(username=REQUESTER_USERNAME)
        self.requester.set_password(REQUESTER_PASSWORD)
        self.requester.save()
        permission = Permission.objects.get(codename=u'is_requester')
        self.requester.user_permissions.add(permission)
        Profile.objects.create(user=self.requester)
        self.requester.save()

    def tearDown(self):
        Requestion.objects.all().delete()
        SadikGroup.objects.all().delete()
        Sadik.objects.all().delete()
        User.objects.all().delete()

    def test_queue_response_code(self):
        client = Client()
        anonym_response = client.get(reverse('anonym_queue'))
        self.assertEqual(anonym_response.status_code, 403)

        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)
        anonym_response = client.get(reverse('anonym_queue'))
        self.assertEqual(anonym_response.status_code, 200)

        login = client.login(username=OPERATOR_USERNAME,
                             password=OPERATOR_PASSWORD)
        self.assertTrue(login)
        operator_response = client.get(reverse('anonym_queue'))
        self.assertEqual(operator_response.status_code, 200)
        client.logout()

        login = client.login(username=REQUESTER_USERNAME,
                             password=REQUESTER_PASSWORD)
        self.assertTrue(login)
        requester_response = client.get(reverse('anonym_queue'))
        self.assertEqual(requester_response.status_code, 200)

    def test_queue_context(self):
        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)

        # провека количества заявок в контексте от лица анонимного пользователя
        anonym_response = self.client.get(reverse('anonym_queue'))
        self.assertEqual(anonym_response.status_code, 200)
        self.assertEqual(anonym_response.context_data["requestions"].count(),
                         Requestion.objects.queue().count())

        # от оператора
        login = self.client.login(
            username=OPERATOR_USERNAME,
            password=OPERATOR_PASSWORD
        )
        self.assertTrue(login)
        operator_response = self.client.get(reverse('anonym_queue'))
        self.assertEqual(operator_response.status_code, 200)
        self.assertEqual(operator_response.context_data["requestions"].count(),
                         Requestion.objects.queue().count())
        self.client.logout()

        # от подтверженного пользователя
        login = self.client.login(
            username=REQUESTER_USERNAME,
            password=REQUESTER_PASSWORD
        )
        self.assertTrue(login)
        requester_response = self.client.get(reverse('anonym_queue'))
        self.assertEqual(requester_response.status_code, 200)
        self.assertEqual(
            requester_response.context_data["requestions"].count(),
            Requestion.objects.queue().count())

    def test_status(self):
        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)

        # Проверям фильтр без указания статуса
        response = self.client.get(reverse('anonym_queue'))
        self.assertEqual(response.context_data["requestions"].count(),
                         Requestion.objects.queue().count())
        for v in response.context_data["requestions"]:
            self.assertIn(
                v.status,
                [STATUS_REQUESTER, STATUS_REQUESTER_NOT_CONFIRMED])

        # Проверям фильтр со статсуом 17( Снят с учёта )
        requestion = Requestion.objects.order_by('?')[0]
        requestion.status = STATUS_REMOVE_REGISTRATION
        requestion.save()

        response = self.client.get(
            reverse('anonym_queue'), data={'status': [17]})
        self.assertEqual(response.context_data["requestions"].count(),
                         Requestion.objects.filter(
                             status=STATUS_REMOVE_REGISTRATION).count())
        for v in response.context_data["requestions"]:
            self.assertEqual(v.status, STATUS_REMOVE_REGISTRATION)

        # Проверяем фильтр со статусом, отсутсвущем в списке
        # в случае, если записей с таким фильтром нет,
        # то он вернет все записи
        response = self.client.get(
            reverse('anonym_queue'),
            data={'status': [STATUS_NOT_APPEAR],  'Benefit_category': 1})

        self.assertFalse(response.context_data['requestions'])

    def test_date_range(self):
        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)
        strptime = datetime.datetime.strptime
        filter_val = [None, None]
        data = dict()

        date_max = datetime.date(2013, 01, 01)
        date_min = datetime.date(2013, 01, 03)

        requestion = Requestion.objects.order_by('?')[0]
        requestion.birth_date = date_min
        requestion.save()

        requestion = Requestion.objects.order_by('?')[1]
        requestion.birth_date = date_max
        requestion.save()

        login = self.client.login(
            username=OPERATOR_USERNAME,
            password=OPERATOR_PASSWORD
        )
        self.assertTrue(login)

        # проверить дипазон только с минимальным значением
        data['birth_date_0'] = date_min.strftime('%d.%m.%Y')
        data['birth_date_1'] = ''
        response = self.client.get(reverse('anonym_queue'), data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__gte=date_min).count())
        for requestion in response.context_data['requestions']:
            self.assertGreaterEqual(requestion.birth_date, date_min)

        # проверить диапазон только с максимальным значением
        data['birth_date_0'] = ''
        data['birth_date_1'] = date_max.strftime('%d.%m.%Y')
        response = self.client.get(reverse('anonym_queue'), data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__lte=date_max).count())
        for requestion in response.context_data['requestions']:
            self.assertLessEqual(requestion.birth_date, date_max)

        # проверить диапазон, располагающийся перед доступным диапазоном
        data['birth_date_0'] = '01.09.1939'
        data['birth_date_1'] = '02.09.1945'
        response = self.client.get(reverse('anonym_queue'), data)

        filter_val[0] = strptime(data['birth_date_0'], '%d.%m.%Y')
        filter_val[1] = strptime(data['birth_date_1'], '%d.%m.%Y')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__range=filter_val).count())

        # проверить диапазон, располагающийся после доступного диапазоном
        data['birth_date_0'] = '01.01.3000'
        data['birth_date_1'] = '01.01.3001'
        response = self.client.get(reverse('anonym_queue'), data)

        filter_val[0] = strptime(data['birth_date_0'], '%d.%m.%Y')
        filter_val[1] = strptime(data['birth_date_1'], '%d.%m.%Y')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__range=filter_val).count())

        # проверить диапазон, частично располагающийся
        # перед доступным диапазоном
        data['birth_date_0'] = '01.09.1939'
        data['birth_date_1'] = date_min.strftime('%d.%m.%Y')
        response = self.client.get(reverse('anonym_queue'), data)

        filter_val[0] = strptime(data['birth_date_0'], '%d.%m.%Y')
        filter_val[1] = date_min
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__range=filter_val).count())

        # проверить диапазон, частично располагающийся
        # после доступного диапазона
        data['birth_date_0'] = date_max.strftime('%d.%m.%Y')
        data['birth_date_1'] = '01.01.3001'
        response = self.client.get(reverse('anonym_queue'), data)

        filter_val[0] = date_max
        filter_val[1] = strptime(data['birth_date_1'], '%d.%m.%Y')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__range=filter_val).count())

        # проверить диапазон, которйы выходит за границы доступного
        data['birth_date_0'] = '01.09.1939'
        data['birth_date_1'] = '01.01.3001'
        response = self.client.get(reverse('anonym_queue'), data)

        filter_val[0] = strptime(data['birth_date_0'], '%d.%m.%Y')
        filter_val[1] = strptime(data['birth_date_1'], '%d.%m.%Y')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__range=filter_val).count())

        # проверить диапазон с одинаковыми значениями
        data['birth_date_0'] = date_min.strftime('%d.%m.%Y')
        data['birth_date_1'] = date_min.strftime('%d.%m.%Y')
        response = self.client.get(reverse('anonym_queue'), data)

        filter_val[0] = filter_val[1] = date_min
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__range=filter_val).count())

        # проверить нормальный диапазон
        data['birth_date_0'] = date_min.strftime('%d.%m.%Y')
        data['birth_date_1'] = date_max.strftime('%d.%m.%Y')
        response = self.client.get(reverse('anonym_queue'), data)

        filter_val[0] = date_min
        filter_val[1] = date_max
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__range=filter_val).count())

        # проверить диапазон в обратном порядке
        data['birth_date_0'] = date_max.strftime('%d.%m.%Y'),
        data['birth_date_1'] = date_min.strftime('%d.%m.%Y')
        response = self.client.get(reverse('anonym_queue'), data)

        filter_val[0] = date_max
        filter_val[1] = date_min
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['requestions'].count(),
                         Requestion.objects.filter(
                             birth_date__range=filter_val).count())
        for requestion in response.context_data['requestions']:
            self.assertIn(requestion.birth_date, [date_min, date_max])

    def test_operator_visibility(self):
        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)
        login = self.client.login(
            username=OPERATOR_USERNAME,
            password=OPERATOR_PASSWORD
        )
        self.assertTrue(login)

        response = self.client.get('/queue/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('birth_date', response.context_data['form'].fields)
