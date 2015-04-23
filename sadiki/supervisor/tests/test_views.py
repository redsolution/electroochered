# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.core import management
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import Client
from django.test.testcases import TestCase
from sadiki.core.models import Requestion, Profile, STATUS_REQUESTER, Address, \
    Area, Sadik, REQUESTION_IDENTITY, AgeGroup, SadikGroup, STATUS_DECISION, \
    Preference, PREFERENCE_IMPORT_FINISHED, STATUS_SHORT_STAY, \
    STATUS_ON_DISTRIBUTION, Distribution, DISTRIBUTION_STATUS_INITIAL, \
    DISTRIBUTION_STATUS_ENDING, STATUS_DISTRIBUTED_FROM_ES
from sadiki.core.permissions import OPERATOR_GROUP_NAME, \
    SADIK_OPERATOR_GROUP_NAME, DISTRIBUTOR_GROUP_NAME, SUPERVISOR_GROUP_NAME
from sadiki.core.utils import get_current_distribution_year
from sadiki.core.tests.utils import create_requestion
from sadiki.distribution.views import DecisionManager


SUPERVISOR_USERNAME = "supervisor"
SUPERVISOR_PASSWORD = "password"


class TestSupervisorViews(TestCase):
    fixtures = ['sadiki/core/fixtures/test_initial.json', ]

    def setUp(self):
        management.call_command('update_initial_data')
        management.call_command('generate_sadiks', 1)

        address = Address.objects.create(
            postindex=123456, street=u'ул.Кирова', building_number=17, )
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
        self.supervisor = User(username=SUPERVISOR_USERNAME)
        self.supervisor.set_password(SUPERVISOR_PASSWORD)
        self.supervisor.save()
        Profile.objects.create(user=self.supervisor)
        supervisor_group = Group.objects.get(name=SUPERVISOR_GROUP_NAME)
        self.supervisor.groups = (supervisor_group,)

    def test_distributed_requester_transitions(self):
        requestion = create_requestion(status=STATUS_REQUESTER)
        requestion.status = STATUS_ON_DISTRIBUTION
        requestion.save()
        requestion.status = STATUS_DECISION
        requestion.save()
        requestion.status = STATUS_DISTRIBUTED_FROM_ES
        requestion.save()
        self.assertEqual(requestion.status, STATUS_DISTRIBUTED_FROM_ES)

        req_url = reverse('supervisor_requestion_info', args=(requestion.id, ))
        req_action_url = reverse(
            'supervisor_requestion_status_change',
            args=(requestion.id, STATUS_REQUESTER))

        login = self.client.login(
            username=SUPERVISOR_USERNAME, password=SUPERVISOR_PASSWORD)
        self.assertTrue(login)
        response = self.client.get(req_url)
        self.assertEqual(response.status_code, 200)
        btn_code = u'<a class="btn" href="{}">Повторная постановка на учет</a>'
        self.assertIn(btn_code.format(
            req_action_url), response.content.decode('utf8'))

