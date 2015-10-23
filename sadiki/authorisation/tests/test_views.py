# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.utils import timezone

from sadiki.core.models import (Preference, Profile, PersonalDocument,
    PREFERENCE_IMPORT_FINISHED)


class CoreViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(CoreViewsTest, cls).setUpClass()
        management.call_command('update_initial_data')
        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)

    @classmethod
    def tearDownClass(cls):
        Permission.objects.all().delete()
        Group.objects.all().delete()
        Preference.objects.all().delete()
        super(CoreViewsTest, cls).tearDownClass()

    def tearDown(self):
        Profile.objects.all().delete()
        User.objects.all().delete()

    def test_registration(self):
        registration_path = reverse('anonym_registration')

        # эмулируем запрос с неотмеченным checkbox
        post_data = {
            'password1': '123456q',
            'password2': '123456q',
            'pdata_processing_permit': '',
        }
        response = self.client.post(registration_path, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Profile.objects.exists())
        self.assertFalse(User.objects.exists())
        reg_form = response.context_data.get('registration_form')
        self.assertIn('pdata_processing_permit', reg_form.errors)

        # запрос с несовпадающими паролями
        post_data = {
            'password1': '123456',
            'password2': '123457',
            'pdata_processing_permit': 'on',
        }
        response = self.client.post(registration_path, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Profile.objects.exists())
        self.assertFalse(User.objects.exists())
        reg_form = response.context_data.get('registration_form')
        self.assertIn('password2', reg_form.errors)

        # запрос с коротким паролем
        post_data = {
            'password1': '123',
            'password2': '123',
            'pdata_processing_permit': 'on',
        }
        response = self.client.post(registration_path, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Profile.objects.exists())
        self.assertFalse(User.objects.exists())
        reg_form = response.context_data.get('registration_form')
        self.assertIn('password1', reg_form.errors)

        # корректный запрос
        post_data = {
            'password1': '123456q',
            'password2': '123456q',
            'pdata_processing_permit': 'on',
        }
        response = self.client.post(registration_path, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('account_frontpage'))
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        new_profile = response.context_data.get('profile')
        self.assertIsInstance(new_profile, Profile)
        new_user = new_profile.user
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']),
                         new_user.pk)
        self.assertTrue(new_user.is_requester())
        self.assertIsNotNone(new_profile.pd_processing_permit)
        time_diff = timezone.now() - new_profile.pd_processing_permit
        min_time_diff = datetime.timedelta(0)
        max_time_diff = datetime.timedelta(minutes=5)
        self.assertTrue(min_time_diff <= time_diff <= max_time_diff)
