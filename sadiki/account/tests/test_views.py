# -*- coding: utf-8 -*-
from django.test import TestCase
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
        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)
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

        self.requester = User.objects.create_user(username='requester',
                                                  password='123456q')
        permission = Permission.objects.get(codename=u'is_requester')
        self.requester.user_permissions.add(permission)
        Profile.objects.create(user=self.requester)
        self.requester.save()

    def tearDown(self):
        Requestion.objects.all().delete()
        SadikGroup.objects.all().delete()
        Sadik.objects.all().delete()
        User.objects.all().delete()

    def test_account_frontpage(self):
        self.assertTrue(self.requester.is_requester())
        login = self.client.login(username=self.requester.username,
                                  password='123456q')
        self.assertTrue(login)
        frontpage_response = self.client.get(reverse('account_frontpage'))
        self.assertEqual(frontpage_response.status_code, 200)
        self.assertTrue(self.requester.username in frontpage_response.content)
        self.client.logout()

    def test_email_add(self):
        self.assertFalse(self.requester.email)

        profile = self.requester.get_profile()
        self.assertFalse(profile.email_verified)

        login = self.client.login(username=self.requester.username,
                                  password='123456q')
        # add new email
        self.assertTrue(login)
        email = 'testmail@gmail.com'
        response = self.client.post(
            reverse('email_change'),
            {'email': email},
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        u = User.objects.get(pk=self.requester.id)
        self.assertEqual(u.email, email)
        self.assertEqual(response.content, '{"ok": true}')
        self.assertFalse(profile.email_verified)
        self.client.logout()

        # TODO: confim mail by operator
        self.client.login(username=self.operator.username, password="password")
        op_resp = self.client.get(reverse('operator_profile_info',
                                          args=[profile.id]))
        self.assertEqual(op_resp.status_code, 200)
        self.assertIn(email, op_resp.content)
        # change by operator
        # change by user
        # confirm by user
