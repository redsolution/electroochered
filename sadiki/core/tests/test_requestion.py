# -*- coding: utf-8 -*-
import random
import datetime
from django.test import TestCase, Client
from django.core import management
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.db.models import Q

from sadiki.core.tests.utils import create_requestion
from sadiki.core.models import Profile, BenefitCategory, Requestion, Sadik, \
    SadikGroup, Preference, PREFERENCE_IMPORT_FINISHED, \
    Address, RequestionQuerySet, STATUS_NOT_APPEAR,  STATUS_REQUESTER, \
    STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REMOVE_REGISTRATION
from sadiki.core.permissions import OPERATOR_GROUP_NAME, \
    SUPERVISOR_GROUP_NAME, SADIK_OPERATOR_GROUP_NAME, DISTRIBUTOR_GROUP_NAME
from sadiki.core.workflow import workflow, CONFIRM_REQUESTION, \
    NOT_CONFIRMED_REMOVE_REGISTRATION, REQUESTION_REJECT


OPERATOR_USERNAME = 'operator'
OPERATOR_PASSWORD = 'password'

SUPERVISOR_USERNAME = 'supervisor'
SUPERVISOR_PASSWORD = 'password'

REQUESTER_USERNAME = 'requester'
REQUESTER_PASSWORD = '1234'


class BaseRequestionTest(TestCase):
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
        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)

    def tearDown(self):
        Requestion.objects.all().delete()
        SadikGroup.objects.all().delete()
        Sadik.objects.all().delete()
        User.objects.all().delete()

    def test_requestion_not_confirmed(self):
        kg = Sadik.objects.all()[0]
        requestion = create_requestion()
        requestion.pref_sadiks.add(kg)
        requestion.save()
        self.assertEqual(requestion.status, STATUS_REQUESTER_NOT_CONFIRMED)

        # проверяем допустимые переводы для неподтвержденной заявки
        transition_indexes = workflow.available_transitions(
            src=requestion.status)
        self.assertEqual(len(transition_indexes), 3)
        self.assertEqual(transition_indexes.sort(), [
            CONFIRM_REQUESTION,
            NOT_CONFIRMED_REMOVE_REGISTRATION,
            REQUESTION_REJECT
        ].sort())
        transitions = requestion.available_transitions()
        self.assertEqual(transition_indexes.sort(),
                         [t.index for t in transitions].sort())
        self.assertTrue(requestion.is_available_for_actions)

        # банальные проверки работы веб-интерфейса
        login = self.client.login(
            username=OPERATOR_USERNAME,
            password=OPERATOR_PASSWORD
        )
        self.assertTrue(login)
        op_response = self.client.get(
            reverse('operator_requestion_info', args=(requestion.id, )))
        self.assertEqual(op_response.status_code, 200)
        self.assertEqual(op_response.context['requestion'], requestion)

        # проверяем доступность разрешенных пользователю транзакций
        user_allowed_transactions = [
            t for t in transitions if t.required_permissions]
        for t in user_allowed_transactions:
            url = reverse(
                'operator_requestion_status_change',
                args=(requestion.id, t.dst)
            )
            t_response = self.client.get(url)
            self.assertEqual(t_response.status_code, 200)
            # проверяем, что кнопка выполнения транзакций пристутствует
            html_button = '<a class="btn" href="{}">'.format(url)
            self.assertIn(html_button, op_response.content)

        # проверяем запрет для пользователя остальных транзакций
        # формируем список из запрещенных транзаций
        user_forbidden_transactions = [
            t for t in transitions if t not in user_allowed_transactions]
        allowed_dst = [t.dst for t in transitions]
        wrong_transitions = [
            t for t in workflow.transitions if (
                t.src != requestion.status and t.dst not in allowed_dst)
        ]
        for t in wrong_transitions + user_forbidden_transactions:
            url = reverse(
                'operator_requestion_status_change',
                args=(requestion.id, t.dst)
            )
            t_response = self.client.get(url)
            self.assertEqual(t_response.status_code, 403)
            # проверяем, что кнопка выполнения транзакций отсутствует
            html_button = '<a class="btn" href="{}">'.format(url)
            self.assertNotIn(html_button, op_response.content)
