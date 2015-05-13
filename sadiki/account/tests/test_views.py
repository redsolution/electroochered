# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core import management
from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse

from sadiki.core.models import Profile, BenefitCategory, Requestion, Sadik, \
    SadikGroup, Preference, PREFERENCE_IMPORT_FINISHED, Address
from sadiki.core.permissions import OPERATOR_GROUP_NAME, SUPERVISOR_GROUP_NAME,\
    SADIK_OPERATOR_GROUP_NAME, DISTRIBUTOR_GROUP_NAME
from sadiki.authorisation.models import VerificationKey


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
        self.requester.email = 'testmail@example.com'
        self.requester.save()
        login = self.client.login(username=self.requester.username,
                                  password='123456q')
        self.assertTrue(login)
        frontpage_response = self.client.get(reverse('account_frontpage'))
        self.assertEqual(frontpage_response.status_code, 200)
        self.assertTrue(self.requester.username in frontpage_response.content)
        self.assertIn(self.requester.email, frontpage_response.content)
        self.client.logout()

    def test_email_add(self):
        """
        Проверка основных операций с почтой
        """

        self.assertFalse(self.requester.email)
        profile = self.requester.get_profile()
        self.assertFalse(profile.email_verified)
        login = self.client.login(username=self.requester.username,
                                  password='123456q')
        self.assertTrue(login)

        # add new email
        email = 'testmail@gmail.com'
        response = self.client.post(
            reverse('email_change'),
            {'email': email},
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        u = User.objects.get(pk=self.requester.id)
        profile = u.get_profile()
        self.assertEqual(u.email, email)
        self.assertEqual(response.content, '{"ok": true}')
        self.assertFalse(profile.email_verified)
        self.client.logout()

        # confirm email by operator
        self.client.login(username=self.operator.username, password="password")
        self.assertTrue(login)
        op_resp = self.client.get(reverse('operator_profile_info',
                                          args=[profile.id]))
        self.assertEqual(op_resp.status_code, 200)
        self.assertIn(email, op_resp.content)
        op_confirm = self.client.get(reverse('confirm_profile_email',
                                             args=[profile.id]))
        self.assertEqual(op_confirm.status_code, 200)
        u = User.objects.get(pk=self.requester.id)
        profile = u.get_profile()
        self.assertTrue(profile.email_verified)

        # change email by operator
        email_by_op = 'newmail@example.com'
        op_change = self.client.post(
            reverse('change_profile_email', args=[profile.id]),
            {'email': email_by_op},
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(op_change.status_code, 200)
        self.assertEqual(response.content, '{"ok": true}')
        u = User.objects.get(pk=self.requester.id)
        profile = u.get_profile()
        self.assertTrue(profile.email_verified)
        self.assertEqual(u.email, email_by_op)
        self.client.logout()

        # change email by user
        login = self.client.login(username=self.requester.username,
                                  password='123456q')
        self.assertTrue(login)
        changed_email = 'changed_email@example.com'
        response = self.client.post(
            reverse('email_change'),
            {'email': changed_email},
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        u = User.objects.get(pk=self.requester.id)
        profile = u.get_profile()
        self.assertEqual(u.email, changed_email)
        self.assertEqual(response.content, '{"ok": true}')
        self.assertFalse(profile.email_verified)

        # confirm email by user
        verification_keys = VerificationKey.objects.filter(user=self.requester)
        key = verification_keys.reverse()[0]
        self.assertTrue(key.is_valid)
        ver_response = self.client.get(reverse('email_verification',
                                               args=[key.key]))
        self.assertTrue(ver_response.status_code, 200)
        u = User.objects.get(pk=self.requester.id)
        profile = u.get_profile()
        self.assertTrue(profile.email_verified)
        self.assertEqual(u.email, changed_email)
        self.client.logout()

        # login with email
        login = self.client.login(username=changed_email, password='123456q')
        self.assertTrue(login)

    def test_email_errors(self):
        """
        Проверка "неправильных" вариантов операций с почтой
        """
        email = 'testmail@example.com'
        self.requester.email = email
        self.requester.save()

        self.assertTrue(self.client.login(username=self.requester.username,
                                          password='123456q'))
        self.client.logout()

        # impossible login with unverified email
        u = User.objects.get(pk=self.requester.id)
        profile = u.get_profile()
        self.assertFalse(profile.email_verified)
        self.assertFalse(self.client.login(username=email,
                                           password='123456q'))

        # unable to post incorrect email
        self.client.login(username=self.requester.username, password='123456q')
        response = self.client.post(
            reverse('email_change'),
            {'email': 'wrong@email'},
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('errors', response.content)
        self.assertIn('"ok": false', response.content)

        # 404 error on wrong verification key
        response_wrong_vkey = self.client.get(reverse('email_verification',
                                              args=['1a2b'*10]))
        self.assertEqual(response_wrong_vkey.status_code, 404)
        self.client.logout()

        # unable to register same email twice
        self.requester1 = User.objects.create_user(username='requester1',
                                                   password='123456q')
        permission = Permission.objects.get(codename=u'is_requester')
        self.requester1.user_permissions.add(permission)
        Profile.objects.create(user=self.requester1)
        self.requester1.save()
        login = self.client.login(username=self.requester1.username,
                                  password='123456q')
        self.assertTrue(login)
        response = self.client.post(
            reverse('email_change'),
            {'email': email},
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('errors', response.content)
        self.assertIn('"ok": false', response.content)
        self.client.logout()

        # check wrong (forbidden) requests
        self.client.login(username=self.operator.username, password="password")
        op_confirm = self.client.post(reverse('confirm_profile_email',
                                              args=[profile.id]))
        self.assertEqual(op_confirm.status_code, 405)

        op_change = self.client.get(
            reverse('change_profile_email', args=[profile.id]),
            {'email': 'somemail@example.com'},
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(op_change.status_code, 405)

    def test_requestion_add(self):
        u"""
        Проверяем корректрость работы ключа token, хранящегося в сессии
        пользователя.
        """
        # отключаем запросы к внешним api во время тестирования
        settings.TEST_MODE = True

        management.call_command('generate_sadiks', 10)
        kgs = Sadik.objects.all()
        form_data = {'name': 'Ann',
                     'sex': 'Ж',
                     'birth_date': '07.06.2014',
                     'admission_date': '01.01.2014',
                     'template': '2',
                     'document_number': 'II-ИВ 016809',
                     'areas': '1',
                     'location': 'POINT (60.115814208984375 55.051432600719835)',
                     'pref_sadiks': [str(kgs[0].id), str(kgs[1].id)],
                     }
        self.assertTrue(self.client.login(username=self.requester.username,
                                          password='123456q'))
        # до посещения страницы с формой, токена нет
        self.assertIsNone(self.client.session.get('token'))
        # заявка не сохраняется, редирект на страницу, с которой пришли
        create_response = self.client.post(
            reverse('requestion_add_by_user'), form_data)
        self.assertEqual(create_response.status_code, 302)
        self.assertRedirects(create_response,
                             reverse('requestion_add_by_user'))
        # после редиректа токен появляется
        self.assertIsNotNone(self.client.session.get('token'))
        self.client.session.flush()
        self.assertIsNone(self.client.session.get('token'))

        # зашли на страницу с формой, токен появился
        self.client.login(username=self.requester.username, password='123456q')
        response = self.client.get(reverse('requestion_add_by_user'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(self.client.session.get('token', None))
        token = response.context['form']['token'].value()
        self.assertIn(token, self.client.session['token'].keys())

        # успешный post, создается заявка, токен не удаляется
        form_data.update({'name': 'Ann',
                          'document_number': 'II-ИВ 016807',
                          'token': token, })
        create_response = self.client.post(
            reverse('requestion_add_by_user'), form_data)
        self.assertEqual(create_response.status_code, 302)
        created_requestion = create_response.context['requestion']
        self.assertRedirects(
            create_response,
            reverse('account_requestion_info', args=(created_requestion.id,)))
        self.assertIsNotNone(self.client.session.get('token', None))
        self.assertEqual(self.client.session['token'][token],
                         created_requestion.id)

        # пробуем post со старым токеном, перенаправляет на заявку по id,
        # хранящемуся по этому токену, если такая имеется
        form_data.update({'name': 'Mary',
                          'document_number': 'II-ИВ 016809',
                          'token': token, })
        create_response = self.client.post(
            reverse('requestion_add_by_user'), form_data)
        self.assertEqual(create_response.status_code, 302)
        self.assertRedirects(
            create_response,
            reverse('account_requestion_info', args=(created_requestion.id,)))
        self.assertIsNotNone(self.client.session.get('token'))

        # пробуем post с неверным токеном, перенаправляет страницу регистрации
        form_data.update({'name': 'Mary',
                          'document_number': 'II-ИВ 016805',
                          'token': 'some-wrong-token', })
        create_response = self.client.post(
            reverse('requestion_add_by_user'), form_data)
        self.assertEqual(create_response.status_code, 302)
        self.assertRedirects(
            create_response, reverse('requestion_add_by_user',))
        self.assertIsNotNone(self.client.session.get('token'))

        # после посещения страницы добавления заявки добавляется еще 1 токен
        self.assertEqual(len(self.client.session['token']), 2)
        response = self.client.get(reverse('requestion_add_by_user'))
        self.assertEqual(len(self.client.session['token']), 3)
        token = response.context['form']['token'].value()
        self.assertIn(token, self.client.session['token'].keys())
        self.assertIsNone(self.client.session['token'][token])

        settings.TEST_MODE = False
