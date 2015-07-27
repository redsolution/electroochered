# -*- coding: utf-8 -*-
import datetime

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
from sadiki.logger.models import Logger, ANONYM_LOG, ACCOUNT_LOG
from sadiki.core.workflow import CHANGE_PERSONAL_DATA, \
    CHANGE_PERSONAL_DATA_BY_OPERATOR, ACCOUNT_CHANGE_REQUESTION, \
    REQUESTION_ADD_BY_REQUESTER, REQUESTION_REGISTRATION_BY_OPERATOR


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
                     'child_last_name': 'Jordison',
                     'sex': 'Ж',
                     'birth_date': '07.06.2014',
                     'admission_date': '01.01.2014',
                     'template': '2',
                     'document_number': 'II-ИВ 016809',
                     'birthplace': 'Chelyabinsk',
                     'kinship_type': 1,
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

    def test_profile_personal_data_actions(self):
        u"""
        Проверка корректности добавления и изменения персональных данных
        в профиле пользователя. Проверка наличия логов и их содержимого
        """
        settings.TEST_MODE = True
        profile = self.requester.profile
        account_frontpage_url = reverse('account_frontpage')
        operator_profile_info_url = reverse('operator_profile_info',
                                            args=(profile.id,))
        profile_form_data = {
            'last_name': 'Jordison',
            'first_name': 'Ann',
            'town': 'New York',
            'street': '1st avenue',
            'house': '100',
            'profile': profile.id,
            'doc_type': 2,
            'series': '1234',
            'number': '654321',
            'issued_date': '30.03.2012',
            'issued_by': 'some_organization',
        }
        # ----- тестируем изменение персональных данных пользователем -----
        self.assertTrue(self.client.login(username=self.requester.username,
                        password='123456q'))
        # проверяем, что данные профиля не заполнены
        self.assertFalse(profile.first_name)
        self.assertFalse(profile.last_name)
        self.assertFalse(profile.middle_name)
        self.assertFalse(profile.mobile_number)
        self.assertFalse(profile.phone_number)
        self.assertFalse(profile.snils)
        self.assertFalse(profile.town)
        self.assertFalse(profile.street)
        self.assertFalse(profile.house)
        profile_documents = profile.personaldocument_set
        self.assertFalse(profile_documents.exists())

        # заполняем данные. намеренно добавляем лишние пробелы к полям
        profile_form_data.update({'first_name': '  Ann ', 'house': ' 100  '})
        response = self.client.post(account_frontpage_url, profile_form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, account_frontpage_url)
        profile_form_data.update({'first_name': 'Ann', 'series': '123456'})
        # проверяем отсутствие ошибок форм
        pdata_form = response.context['pdata_form']
        doc_form = response.context['doc_form']
        self.assertFalse(pdata_form.errors)
        self.assertFalse(doc_form.errors)
        # проверяем изменение данных
        changed_profile = Profile.objects.get(id=profile.id)
        self.assertEqual(changed_profile.first_name, 'Ann')
        self.assertEqual(changed_profile.last_name, 'Jordison')
        self.assertFalse(changed_profile.middle_name)
        self.assertFalse(changed_profile.mobile_number)
        self.assertFalse(changed_profile.phone_number)
        self.assertFalse(changed_profile.snils)
        self.assertEqual(changed_profile.town, 'New York')
        self.assertEqual(changed_profile.street, '1st avenue')
        self.assertEqual(changed_profile.house, '100')
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 2)
        self.assertEqual(profile_document.series, '1234')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        self.assertEqual(profile_document.issued_by, 'some_organization')
        # проверяем логи
        logs = Logger.objects.filter(
            action_flag=CHANGE_PERSONAL_DATA).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertIn('Ann', log_message)
        self.assertIn('Jordison', log_message)
        self.assertIn('New York', log_message)
        self.assertIn('1st avenue', log_message)
        self.assertIn('100', log_message)
        self.assertIn(u'Паспорт', log_message)
        self.assertIn('1234', log_message)
        self.assertIn('654321', log_message)
        self.assertIn('30.03.2012', log_message)
        self.assertIn('some_organization', log_message)
        last_log.delete()

        # пытаемся сохранить документ типа "иное" без названия
        profile_form_data.update({'doc_type': 1})
        response = self.client.post(account_frontpage_url , profile_form_data)
        self.assertEqual(response.status_code, 200)
        # проверяем ошибки форм
        pdata_form = response.context['pdata_form']
        doc_form = response.context['doc_form']
        self.assertFalse(pdata_form.errors)
        self.assertIn('doc_name', doc_form.errors)
        self.assertIn(u'Обязательное поле', doc_form.errors['doc_name'])
        # проверяем, что документ не сохранился
        changed_profile = Profile.objects.get(id=profile.id)
        self.assertEqual(changed_profile.first_name, 'Ann')
        self.assertEqual(changed_profile.last_name, 'Jordison')
        self.assertFalse(changed_profile.middle_name)
        self.assertFalse(changed_profile.mobile_number)
        self.assertFalse(changed_profile.phone_number)
        self.assertFalse(changed_profile.snils)
        self.assertEqual(changed_profile.town, 'New York')
        self.assertEqual(changed_profile.street, '1st avenue')
        self.assertEqual(changed_profile.house, '100')
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 2)
        self.assertEqual(profile_document.series, '1234')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        self.assertEqual(profile_document.issued_by, 'some_organization')
        # проверяем отсутствие логов
        logs = Logger.objects.filter(
            action_flag=CHANGE_PERSONAL_DATA).order_by('-datetime')
        self.assertFalse(logs.exists())

        # теперь добавляем название документа, + убираем необязательные поля
        profile_form_data.update({'doc_name': 'test_document',
                                  'series': '',
                                  'issued_by': ''})
        response = self.client.post(account_frontpage_url, profile_form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, account_frontpage_url)
        # проверяем отсутствие ошибок форм
        pdata_form = response.context['pdata_form']
        doc_form = response.context['doc_form']
        self.assertFalse(pdata_form.errors)
        self.assertFalse(doc_form.errors)
        # проверяем изменение данных
        changed_profile = Profile.objects.get(id=profile.id)
        self.assertEqual(changed_profile.first_name, 'Ann')
        self.assertEqual(changed_profile.last_name, 'Jordison')
        self.assertFalse(changed_profile.middle_name)
        self.assertFalse(changed_profile.mobile_number)
        self.assertFalse(changed_profile.phone_number)
        self.assertFalse(changed_profile.snils)
        self.assertEqual(changed_profile.town, 'New York')
        self.assertEqual(changed_profile.street, '1st avenue')
        self.assertEqual(changed_profile.house, '100')
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 1)
        self.assertEqual(profile_document.series, '')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        self.assertEqual(profile_document.issued_by, '')
        # проверяем логи
        logs = Logger.objects.filter(
            action_flag=CHANGE_PERSONAL_DATA).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertNotIn('Ann', log_message)
        self.assertNotIn('Jordison', log_message)
        self.assertNotIn('New York', log_message)
        self.assertNotIn('1st avenue', log_message)
        self.assertNotIn('100', log_message)
        self.assertIn(u'Паспорт', log_message)
        self.assertIn('1234', log_message)
        self.assertIn('654321', log_message)
        self.assertIn('30.03.2012', log_message)
        self.assertIn('some_organization', log_message)
        self.assertIn('test_document', log_message)
        last_log.delete()

        # меняем имя и добавляем СНИЛС
        profile_form_data.update({'first_name': 'Mary',
                                  'snils': '123-123-123 44'})
        response = self.client.post(account_frontpage_url, profile_form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, account_frontpage_url)
        # проверяем отсутствие ошибок форм
        pdata_form = response.context['pdata_form']
        doc_form = response.context['doc_form']
        self.assertFalse(pdata_form.errors)
        self.assertFalse(doc_form.errors)
        # проверяем изменение данных
        changed_profile = Profile.objects.get(id=profile.id)
        self.assertEqual(changed_profile.first_name, 'Mary')
        self.assertEqual(changed_profile.last_name, 'Jordison')
        self.assertFalse(changed_profile.middle_name)
        self.assertFalse(changed_profile.mobile_number)
        self.assertFalse(changed_profile.phone_number)
        self.assertEqual(changed_profile.snils, '123-123-123 44')
        self.assertEqual(changed_profile.town, 'New York')
        self.assertEqual(changed_profile.street, '1st avenue')
        self.assertEqual(changed_profile.house, '100')
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 1)
        self.assertEqual(profile_document.series, '')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        # проверяем логи
        logs = Logger.objects.filter(
            action_flag=CHANGE_PERSONAL_DATA).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertIn('Ann', log_message)
        self.assertIn('Mary', log_message)
        self.assertIn('123-123-123 44', log_message)
        self.assertNotIn('Jordison', log_message)
        self.assertNotIn('New York', log_message)
        self.assertNotIn('1st avenue', log_message)
        self.assertNotIn('100', log_message)
        self.assertNotIn(u'Паспорт', log_message)
        self.assertNotIn('test_document', log_message)
        self.assertNotIn('654321', log_message)
        self.assertNotIn('30.03.2012', log_message)
        last_log.delete()

        # пытаемся задать некорректный СНИЛС и заодно поменять имя
        profile_form_data.update({'first_name': 'Kate',
                                  'snils': '444-333222 11'})
        response = self.client.post(account_frontpage_url , profile_form_data)
        self.assertEqual(response.status_code, 200)
        # проверяем ошибки форм
        pdata_form = response.context['pdata_form']
        doc_form = response.context['doc_form']
        self.assertFalse(doc_form.errors)
        self.assertNotIn('first_name', pdata_form.errors)
        self.assertIn('snils', pdata_form.errors)
        self.assertIn(u'неверный формат', pdata_form.errors['snils'])
        # проверяем, что ни СНИЛС, ни имя не сохранились
        changed_profile = Profile.objects.get(id=profile.id)
        self.assertEqual(changed_profile.first_name, 'Mary')
        self.assertEqual(changed_profile.last_name, 'Jordison')
        self.assertFalse(changed_profile.middle_name)
        self.assertFalse(changed_profile.mobile_number)
        self.assertFalse(changed_profile.phone_number)
        self.assertEqual(changed_profile.snils, '123-123-123 44')
        self.assertEqual(changed_profile.town, 'New York')
        self.assertEqual(changed_profile.street, '1st avenue')
        self.assertEqual(changed_profile.house, '100')
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 1)
        self.assertEqual(profile_document.series, '')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        # проверяем отсутствие логов
        logs = Logger.objects.filter(
            action_flag=CHANGE_PERSONAL_DATA).order_by('-datetime')
        self.assertFalse(logs.exists())

        # ----- тестируем изменение персональных данных оператором -----
        self.assertTrue(self.client.login(username=self.operator.username,
                        password='password'))

        # меняем адрес, добавляем телефон, возвращаем имя и корректный СНИЛС
        profile_form_data.update({'first_name': 'Mary',
                                  'snils': '123-123-123 44',
                                  'town': 'Chicago', 'street': 'any_street',
                                  'house': 222, 'mobile_number': '777-77-77'})
        response = self.client.post(operator_profile_info_url,
                                    profile_form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, operator_profile_info_url)
        # проверяем отсутствие ошибок форм
        pdata_form = response.context['pdata_form']
        doc_form = response.context['doc_form']
        self.assertFalse(pdata_form.errors)
        self.assertFalse(doc_form.errors)
        # проверяем изменение данных
        changed_profile = Profile.objects.get(id=profile.id)
        self.assertEqual(changed_profile.first_name, 'Mary')
        self.assertEqual(changed_profile.last_name, 'Jordison')
        self.assertFalse(changed_profile.middle_name)
        self.assertEqual(changed_profile.mobile_number, '777-77-77')
        self.assertFalse(changed_profile.phone_number)
        self.assertEqual(changed_profile.snils, '123-123-123 44')
        self.assertEqual(changed_profile.town, 'Chicago')
        self.assertEqual(changed_profile.street, 'any_street')
        self.assertEqual(changed_profile.house, '222')
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 1)
        self.assertEqual(profile_document.series, '')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        # проверяем логи
        logs = Logger.objects.filter(
            action_flag=CHANGE_PERSONAL_DATA_BY_OPERATOR).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertNotIn('Mary', log_message)
        self.assertNotIn('Jordison', log_message)
        self.assertIn('New York', log_message)
        self.assertIn('1st avenue', log_message)
        self.assertIn('100', log_message)
        self.assertIn('Chicago', log_message)
        self.assertIn('any_street', log_message)
        self.assertIn('222', log_message)
        self.assertIn('777-77-77', log_message)
        self.assertNotIn('test_document', log_message)
        self.assertNotIn('654321', log_message)
        self.assertNotIn('30.03.2012', log_message)
        last_log.delete()

        # пытаемся сохранить паспортные данные без обязательных полей
        # + задаём некорректный формат номера
        profile_form_data.update({'doc_type': 2, 'issued_by': '',
                                  'series': '', 'number': 'test'})
        response = self.client.post(operator_profile_info_url,
                                    profile_form_data)
        self.assertEqual(response.status_code, 200)
        # проверяем ошибки форм
        pdata_form = response.context['pdata_form']
        doc_form = response.context['doc_form']
        self.assertFalse(pdata_form.errors)
        self.assertIn('series', doc_form.errors)
        self.assertIn(u'неверный формат', doc_form.errors['series'])
        self.assertIn('number', doc_form.errors)
        self.assertIn(u'неверный формат', doc_form.errors['number'])
        self.assertIn('issued_by', doc_form.errors)
        self.assertIn(u'Обязательное поле', doc_form.errors['issued_by'])
        # проверяем, что документ не сохранился
        changed_profile = Profile.objects.get(id=profile.id)
        self.assertEqual(changed_profile.first_name, 'Mary')
        self.assertEqual(changed_profile.last_name, 'Jordison')
        self.assertFalse(changed_profile.middle_name)
        self.assertEqual(changed_profile.mobile_number, '777-77-77')
        self.assertFalse(changed_profile.phone_number)
        self.assertEqual(changed_profile.snils, '123-123-123 44')
        self.assertEqual(changed_profile.town, 'Chicago')
        self.assertEqual(changed_profile.street, 'any_street')
        self.assertEqual(changed_profile.house, '222')
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 1)
        self.assertEqual(profile_document.series, '')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        # проверяем отсутствие логов
        logs = Logger.objects.filter(
            action_flag=CHANGE_PERSONAL_DATA_BY_OPERATOR).order_by('-datetime')
        self.assertFalse(logs.exists())

        # пытаемся добавить два одинаковых документа (совпадают тип+серия+номер)
        doc_form_data = {'doc_type': 2, 'series': '1234', 'number': '123456',
                         'issued_date': '01.01.2014', 'issued_by': 'test'}
        profile_form_data.update(doc_form_data)
        # сохраняем паспортные данные для текущего профиля
        self.assertTrue(self.client.login(username=self.requester.username,
                                          password='123456q'))
        response = self.client.post(account_frontpage_url, profile_form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, account_frontpage_url)
        # проверяем отсутствие ошибок форм
        pdata_form = response.context['pdata_form']
        doc_form = response.context['doc_form']
        self.assertFalse(pdata_form.errors)
        self.assertFalse(doc_form.errors)
        # проверяем изменение паспортных данных
        changed_profile = Profile.objects.get(id=profile.id)
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 2)
        self.assertEqual(profile_document.series, '1234')
        self.assertEqual(profile_document.number, '123456')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2014, 1, 1))
        self.assertEqual(profile_document.issued_by, 'test')
        # создаём ещё один профиль
        requester2 = User.objects.create_user(username='requester2',
                                              password='123456q')
        permission = Permission.objects.get(codename=u'is_requester')
        requester2.user_permissions.add(permission)
        requester2.save()
        profile2 = Profile.objects.create(user=requester2)
        self.assertTrue(self.client.login(username='requester2',
                                          password='123456q'))
        profile_form_data.update({'profile': profile2.id})
        # пытаемся сохранить те же паспортные данные для нового профиля
        response = self.client.post(account_frontpage_url, profile_form_data)
        self.assertEqual(response.status_code, 200)
        # проверяем ошибки форм
        pdata_form = response.context['pdata_form']
        doc_form = response.context['doc_form']
        self.assertFalse(pdata_form.errors)
        self.assertIn(u'Документ заявителя с таким Тип документа,'
                      u'Серия документа и Номер документа уже существует.',
                      doc_form.non_field_errors())
        # проверяем, что данные не сохранились
        changed_profile = Profile.objects.get(id=profile2.id)
        profile_document = changed_profile.personaldocument_set
        self.assertFalse(profile_document.exists())

        settings.TEST_MODE = False

    def test_requestion_personal_data_actions(self):
        u"""
        Проверка корректности добавления и изменения персональных данных
        заявки.
        """
        settings.TEST_MODE = True
        requestion_add_by_user_url = reverse('requestion_add_by_user')
        management.call_command('generate_sadiks', 1)
        kgs = Sadik.objects.all()
        requestion_form_data = {
            'name': '',
            'child_last_name': 'Jordison',
            'sex': 'Ж',
            'birth_date': '07.06.2014',
            'admission_date': '01.01.2014',
            'template': '2',
            'document_number': 'II-ИВ 016809',
            'birthplace': 'Chelyabinsk',
            'kinship': '',
            'areas': '1',
            'location': 'POINT (60.115814208984375 55.051432600719835)',
            'pref_sadiks': [str(kgs[0].id)],
        }
        # ----- тестируем добавление заявки пользователем -----
        self.client.login(username=self.requester.username, password='123456q')

        # оставляем пустым обязательное поле "имя ребёнка"
        # также пропускаем kinship_type, KeyError не должен возникать
        response = self.client.get(requestion_add_by_user_url)
        token = response.context['form']['token'].value()
        requestion_form_data.update({'token': token, })
        create_response = self.client.post(
            requestion_add_by_user_url, requestion_form_data)
        self.assertEqual(create_response.status_code, 200)
        # проверяем ошибки формы
        requestion_form = create_response.context['form']
        self.assertIn('name', requestion_form.errors)
        self.assertIn(u'Обязательное поле', requestion_form.errors['name'])
        self.assertIn('kinship', requestion_form.errors)
        self.assertIn(u'Обязательное поле', requestion_form.errors['kinship'])
        # проверяем, что заявка не добавилась
        requestions = Requestion.objects.filter(
            profile_id=self.requester.profile.id)
        self.assertFalse(requestions.exists())
        # проверяем отсутствие логов
        logs = Logger.objects.filter(
            action_flag=REQUESTION_ADD_BY_REQUESTER).order_by('-datetime')
        self.assertFalse(logs.exists())

        # добавляем недостающие имя ребёнка и степень родства
        requestion_form_data.update({'name': 'Ann', 'kinship_type': 1})
        response = self.client.get(requestion_add_by_user_url)
        token = response.context['form']['token'].value()
        requestion_form_data.update({'token': token, })
        create_response = self.client.post(
            requestion_add_by_user_url, requestion_form_data, follow=True)
        self.assertIn('requestion', create_response.context)
        created_requestion = create_response.context['requestion']
        requestion_id = created_requestion.id
        requestion_info_url = reverse('account_requestion_info',
                                      args=(created_requestion.id,))
        self.assertEqual(create_response.status_code, 200)
        self.assertRedirects(create_response, requestion_info_url)
        # проверяем сохранение заявки
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.name, 'Ann')
        self.assertEqual(requestion.child_last_name, 'Jordison')
        self.assertEqual(requestion.sex, u'Ж')
        self.assertEqual(requestion.admission_date, datetime.date(2014, 1, 1))
        self.assertEqual(requestion.birth_date, datetime.date(2014, 6, 7))
        self.assertEqual(requestion.birthplace, 'Chelyabinsk')
        self.assertEqual(requestion.kinship, u'Мать')
        evidience_document = requestion.evidience_documents()[0]
        self.assertEqual(evidience_document.document_number, u'II-ИВ 016809')
        # проверяем логи
        logs = Logger.objects.filter(
            action_flag=REQUESTION_ADD_BY_REQUESTER).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertIn('Ann', log_message)
        self.assertIn('Jordison', log_message)
        self.assertIn(u'Женский', log_message)
        self.assertIn('Chelyabinsk', log_message)
        self.assertIn(u'Мать', log_message)
        last_log.delete()

        # изменение добавленной заявки. меняем имя ребёнка, указываем СНИЛС
        change_requestion_form_data = {
            'name': 'Mary',
            'child_last_name': 'Jordison',
            'sex': 'Ж',
            'birth_date': '07.06.2014',
            'admission_date': '01.01.2014',
            'birthplace': 'Chelyabinsk',
            'kinship_type': 1,
            'child_snils': '111-222-333 99',
            'areas': '1',
            'location': 'POINT (60.115814208984375 55.051432600719835)',
            'pref_sadiks': [str(kgs[0].id)],
        }
        response = self.client.post(
            requestion_info_url, change_requestion_form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, requestion_info_url)
        # проверяем отсутствие ошибок формы
        requestion_form = response.context['change_requestion_form']
        self.assertFalse(requestion_form.errors)
        # проверяем изменение данных заявки
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.name, 'Mary')
        self.assertEqual(requestion.child_last_name, 'Jordison')
        self.assertEqual(requestion.sex, u'Ж')
        self.assertEqual(requestion.admission_date, datetime.date(2014, 1, 1))
        self.assertEqual(requestion.birthplace, 'Chelyabinsk')
        self.assertEqual(requestion.kinship, u'Мать')
        self.assertEqual(requestion.child_snils, '111-222-333 99')
        # проверяем логи
        logs = Logger.objects.filter(
            action_flag=ACCOUNT_CHANGE_REQUESTION).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertIn('Mary', log_message)
        self.assertIn('111-222-333 99', log_message)
        self.assertNotIn('Jordison', log_message)
        self.assertNotIn(u'Женский', log_message)
        self.assertNotIn('Chelyabinsk', log_message)
        self.assertNotIn(u'Мать', log_message)
        last_log.delete()

        # пытаемся поменять СНИЛС на некорректный, + имя ребёнка с пробелами
        change_requestion_form_data.update({'child_snils': '111222333',
                                            'name': 'Mary Mary'})
        response = self.client.post(requestion_info_url,
                                    change_requestion_form_data)
        self.assertEqual(response.status_code, 200)
        change_requestion_form_data.update({'child_snils': '111-222-333 99',
                                            'name': 'Mary'})
        # проверяем ошибки формы
        requestion_form = response.context['change_requestion_form']
        self.assertIn('name', requestion_form.errors)
        self.assertIn(u'Поле не должно содержать пробелов',
                      requestion_form.errors['name'])
        self.assertIn('child_snils', requestion_form.errors)
        self.assertIn(u'неверный формат', requestion_form.errors['child_snils'])
        # проверяем, что заявка не изменилась
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.name, 'Mary')
        self.assertEqual(requestion.child_last_name, 'Jordison')
        self.assertEqual(requestion.sex, u'Ж')
        self.assertEqual(requestion.admission_date, datetime.date(2014, 1, 1))
        self.assertEqual(requestion.birthplace, 'Chelyabinsk')
        self.assertEqual(requestion.kinship, u'Мать')
        self.assertEqual(requestion.child_snils, '111-222-333 99')
        # проверяем отсутствие логов
        logs = Logger.objects.filter(
            action_flag=ACCOUNT_CHANGE_REQUESTION).order_by('-datetime')
        self.assertFalse(logs.exists())

        # пытаемся занулить степень родства заявителя
        change_requestion_form_data.update({'kinship_type': 0})
        response = self.client.post(requestion_info_url,
                                    change_requestion_form_data)
        self.assertEqual(response.status_code, 200)
        # проверяем ошибки формы
        requestion_form = response.context['change_requestion_form']
        self.assertNotIn('child_snils', requestion_form.errors)
        self.assertIn('kinship', requestion_form.errors)
        self.assertIn(u'Обязательное поле', requestion_form.errors['kinship'])
        # проверяем, что заявка не изменилась
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.name, 'Mary')
        self.assertEqual(requestion.child_last_name, 'Jordison')
        self.assertEqual(requestion.sex, u'Ж')
        self.assertEqual(requestion.admission_date, datetime.date(2014, 1, 1))
        self.assertEqual(requestion.birthplace, 'Chelyabinsk')
        self.assertEqual(requestion.kinship, u'Мать')
        self.assertEqual(requestion.child_snils, '111-222-333 99')
        # проверяем отсутствие логов
        logs = Logger.objects.filter(
            action_flag=ACCOUNT_CHANGE_REQUESTION).order_by('-datetime')
        self.assertFalse(logs.exists())

        # наконец, задаём собственную степень родства
        change_requestion_form_data.update({'kinship': 'grandfather'})
        response = self.client.post(
            requestion_info_url, change_requestion_form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, requestion_info_url)
        # проверяем отсутствие ошибок формы
        requestion_form = response.context['change_requestion_form']
        self.assertFalse(requestion_form.errors)
        # проверяем изменение данных заявки
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.name, 'Mary')
        self.assertEqual(requestion.child_last_name, 'Jordison')
        self.assertEqual(requestion.sex, u'Ж')
        self.assertEqual(requestion.admission_date, datetime.date(2014, 1, 1))
        self.assertEqual(requestion.birthplace, 'Chelyabinsk')
        self.assertEqual(requestion.kinship, 'grandfather')
        self.assertEqual(requestion.child_snils, '111-222-333 99')
        # проверяем логи
        logs = Logger.objects.filter(
            action_flag=ACCOUNT_CHANGE_REQUESTION).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertNotIn('111-222-333 99', log_message)
        self.assertNotIn('Jordison', log_message)
        self.assertNotIn(u'Женский', log_message)
        self.assertNotIn('Chelyabinsk', log_message)
        self.assertIn('grandfather', log_message)
        last_log.delete()

        # ----- тестируем добавление заявки оператором -----
        self.client.login(username=self.operator.username, password='password')
        profile = self.requester.profile
        response = self.client.get(
            reverse('operator_requestion_add', args=(profile.id,)))
        token = response.context['form']['token'].value()
        requestion_form_data.update({
            'token': token,
            'template': '2',
            'document_number': 'II-ИВ 123321',
            'core-evidiencedocument-content_type-object_id-TOTAL_FORMS': 1,
            'core-evidiencedocument-content_type-object_id-INITIAL_FORMS': 0,
            'core-evidiencedocument-content_type-object_id-MAX_NUM_FORMS': 100,
            'core-evidiencedocument-content_type-object_id-0-id': '',
            'core-evidiencedocument-content_type-object_id-0-template': '',
            'core-evidiencedocument-content_type-object_id-0-document_number':
            ''
        })
        create_response = self.client.post(
            reverse('operator_requestion_add', args=(profile.id,)),
            requestion_form_data, follow=True)
        self.assertIn('requestion', create_response.context)
        created_requestion = create_response.context['requestion']
        requestion_id = created_requestion.id
        self.assertEqual(create_response.status_code, 200)
        self.assertRedirects(
            create_response,
            reverse('operator_requestion_info', args=(requestion_id,)))
        # проверяем сохранение заявки
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.name, 'Ann')
        self.assertEqual(requestion.child_last_name, 'Jordison')
        self.assertEqual(requestion.sex, u'Ж')
        self.assertEqual(requestion.admission_date, datetime.date(2014, 1, 1))
        self.assertEqual(requestion.birth_date, datetime.date(2014, 6, 7))
        self.assertEqual(requestion.birthplace, 'Chelyabinsk')
        self.assertEqual(requestion.kinship, u'Мать')
        evidience_document = requestion.evidience_documents()[0]
        self.assertEqual(evidience_document.document_number, u'II-ИВ 123321')
        # проверяем логи
        logs = Logger.objects.filter(
            action_flag=REQUESTION_REGISTRATION_BY_OPERATOR).order_by(
                '-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertIn('Ann', log_message)
        self.assertIn('Jordison', log_message)
        self.assertIn(u'Женский', log_message)
        self.assertIn('Chelyabinsk', log_message)
        self.assertIn(u'Мать', log_message)
        last_log.delete()

        settings.TEST_MODE = False
