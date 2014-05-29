# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.core import management
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse

from sadiki.core.models import Profile, BenefitCategory, Requestion, Sadik, \
    SadikGroup, Preference, PREFERENCE_IMPORT_FINISHED, Address
from sadiki.core.permissions import OPERATOR_GROUP_NAME, SUPERVISOR_GROUP_NAME,\
    SADIK_OPERATOR_GROUP_NAME, DISTRIBUTOR_GROUP_NAME


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
        self.operator = User(username='operator')
        self.operator.set_password("password")
        self.operator.save()
        Profile.objects.create(user=self.operator)
        operator_group = Group.objects.get(name=OPERATOR_GROUP_NAME)
        sadik_operator_group = Group.objects.get(name=SADIK_OPERATOR_GROUP_NAME)
        distributor_group = Group.objects.get(name=DISTRIBUTOR_GROUP_NAME)
        self.operator.groups = (operator_group, sadik_operator_group,
                                distributor_group)
        self.supervisor = User(username="supervisor")
        self.supervisor.set_password("password")
        self.supervisor.save()
        Profile.objects.create(user=self.supervisor)
        supervisor_group = Group.objects.get(name=SUPERVISOR_GROUP_NAME)
        self.supervisor.groups = (supervisor_group,)

        self.requester = User(username='requester')
        self.requester.set_password('1234')
        self.requester.save()
        permission = Permission.objects.get(codename=u'is_requester')
        self.requester.user_permissions.add(permission)
        Profile.objects.create(user=self.requester)
        self.requester.save()

    def tearDown(self):
        Requestion.objects.all().delete()
        SadikGroup.objects.all().delete()
        Sadik.objects.all().delete()

    def test_queue_response_code(self):
        client = Client()
        anonym_response = client.get(reverse('anonym_queue'))
        self.assertEqual(anonym_response.status_code, 403)

        management.call_command('generate_sadiks', 1)
        management.call_command('generate_requestions', 2,
                                distribute_in_any_sadik=True)
        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)
        anonym_response = client.get(reverse('anonym_queue'))
        self.assertEqual(anonym_response.status_code, 200)

        client.login(username=self.operator.username,
                     password=self.operator.password)
        operator_response = client.get(reverse('anonym_queue'))
        self.assertEqual(operator_response.status_code, 200)
        client.logout()

        client.login(username=self.requester.username,
                     password=self.requester.password)
        requester_response = client.get(reverse('anonym_queue'))
        self.assertEqual(requester_response.status_code, 200)
