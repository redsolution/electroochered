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
        profile_form_data = {
            'last_name': 'Jordison',
            'first_name': 'Ann',
            'town': 'New York',
            'street': '1st avenue',
            'house': '100',
            'profile': profile.id,
            'doc_type': 1,
            'series': '123456',
            'number': '654321',
            'issued_date': '30.03.2012',
            'issued_by': 'some_organization',
        }
        # ----- изменение персональных данных пользователем -----
        self.assertTrue(self.client.login(username=self.requester.username,
                        password='123456q'))
        # заполняем пустую форму
        response = self.client.post(
            reverse('account_frontpage'), profile_form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('account_frontpage'))
        # проверяем изменение данных
        changed_profile = Profile.objects.get(id=self.requester.profile.id)
        self.assertEqual(changed_profile.first_name, 'Ann')
        self.assertEqual(changed_profile.last_name, 'Jordison')
        self.assertEqual(changed_profile.town, 'New York')
        self.assertEqual(changed_profile.street, '1st avenue')
        self.assertEqual(changed_profile.house, '100')
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 1)
        self.assertEqual(profile_document.series, '123456')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        self.assertEqual(profile_document.issued_by, 'some_organization')
        # проверка логов
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
        self.assertIn('123456', log_message)
        self.assertIn('654321', log_message)
        self.assertIn('30.03.2012', log_message)
        self.assertIn('some_organization', log_message)
        last_log.delete()
        # попытка сохранить документ без названия
        profile_form_data.update({'doc_type': 0})
        response = self.client.post(
            reverse('account_frontpage'), profile_form_data)
        self.assertEqual(response.status_code, 200)
        # проверяем, что документ не сохранился
        changed_profile = Profile.objects.get(id=self.requester.profile.id)
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 1)
        self.assertEqual(profile_document.series, '123456')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        self.assertEqual(profile_document.issued_by, 'some_organization')
        # теперь добавляем название документа, + убираем необязательные поля
        profile_form_data.update({'doc_name': 'test_document',
                                  'series': '',
                                  'issued_by': ''})
        response = self.client.post(
            reverse('account_frontpage'), profile_form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('account_frontpage'))
        # проверяем изменение данных
        changed_profile = Profile.objects.get(id=self.requester.profile.id)
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 0)
        self.assertEqual(profile_document.series, '')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        self.assertEqual(profile_document.issued_by, '')
        # проверка логов
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
        self.assertIn('123456', log_message)
        self.assertIn('654321', log_message)
        self.assertIn('30.03.2012', log_message)
        self.assertIn('some_organization', log_message)
        self.assertIn('test_document', log_message)
        last_log.delete()
        # меняем только имя
        profile_form_data.update({'first_name': 'Mary'})
        response = self.client.post(
            reverse('account_frontpage'), profile_form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('account_frontpage'))
        # проверяем изменение данных
        changed_profile = Profile.objects.get(id=self.requester.profile.id)
        self.assertEqual(changed_profile.first_name, 'Mary')
        # проверка логов
        logs = Logger.objects.filter(
            action_flag=CHANGE_PERSONAL_DATA).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertIn('Ann', log_message)
        self.assertIn('Mary', log_message)
        self.assertNotIn('Jordison', log_message)
        self.assertNotIn('New York', log_message)
        self.assertNotIn('1st avenue', log_message)
        self.assertNotIn('100', log_message)
        self.assertNotIn(u'Паспорт', log_message)
        self.assertNotIn('test_document', log_message)
        self.assertNotIn('654321', log_message)
        self.assertNotIn('30.03.2012', log_message)
        last_log.delete()
        # ----- изменение персональных данных оператором -----
        self.assertTrue(self.client.login(username=self.operator.username,
                        password='password'))
        # меняем только адрес
        profile_form_data.update({'town': 'Chicago', 'street': 'any_street',
                                  'house': 222})
        response = self.client.post(
            reverse('operator_profile_info', args=(profile.id,)),
            profile_form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('operator_profile_info',
                                               args=(profile.id,)))
        # проверяем изменение данных
        changed_profile = Profile.objects.get(id=self.requester.profile.id)
        self.assertEqual(changed_profile.town, 'Chicago')
        self.assertEqual(changed_profile.street, 'any_street')
        self.assertEqual(changed_profile.house, '222')
        # проверка логов
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
        self.assertNotIn('test_document', log_message)
        self.assertNotIn('654321', log_message)
        self.assertNotIn('30.03.2012', log_message)
        # попытка сохранить паспортные данные без обязательных полей
        profile_form_data.update({'doc_type': 1})
        response = self.client.post(
            reverse('operator_profile_info', args=(profile.id,)),
            profile_form_data)
        self.assertEqual(response.status_code, 200)
        # проверяем, что документ не сохранился
        changed_profile = Profile.objects.get(id=self.requester.profile.id)
        profile_document = changed_profile.personaldocument_set.all()[0]
        self.assertEqual(profile_document.doc_type, 0)
        self.assertEqual(profile_document.series, '')
        self.assertEqual(profile_document.number, '654321')
        self.assertEqual(profile_document.issued_date,
                         datetime.date(2012, 3, 30))
        self.assertEqual(profile_document.issued_by, '')
        settings.TEST_MODE = False

    def test_requestion_personal_data_actions(self):
        u"""
        Проверка корректности добавления и изменения персональных данных
        заявки.
        """
        settings.TEST_MODE = True
        management.call_command('generate_sadiks', 1)
        kgs = Sadik.objects.all()
        requestion_form_data = {
            'name': 'Ann',
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
            'pref_sadiks': [str(kgs[0].id)],
        }
        # добавление заявки пользователем
        self.client.login(username=self.requester.username, password='123456q')
        response = self.client.get(reverse('requestion_add_by_user'))
        token = response.context['form']['token'].value()
        requestion_form_data.update({'token': token, })
        create_response = self.client.post(
            reverse('requestion_add_by_user'), requestion_form_data,
            follow=True)
        self.assertIn('requestion', create_response.context)
        created_requestion = create_response.context['requestion']
        requestion_id = created_requestion.id
        self.assertEqual(create_response.status_code, 200)
        self.assertRedirects(
            create_response,
            reverse('account_requestion_info', args=(created_requestion.id,)))
        # проверяем сохранение заявки
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.name, 'Ann')
        self.assertEqual(requestion.child_last_name, 'Jordison')
        self.assertEqual(requestion.sex, u'Ж')
        self.assertEqual(requestion.admission_date, datetime.date(2014, 1, 1))
        self.assertEqual(requestion.birth_date, datetime.date(2014, 6, 7))
        self.assertEqual(requestion.birthplace, 'Chelyabinsk')
        self.assertEqual(requestion.kinship, u'мать')
        evidience_document = requestion.evidience_documents()[0]
        self.assertEqual(evidience_document.document_number, u'II-ИВ 016809')
        # проверка логов
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
        self.assertIn(u'мать', log_message)
        last_log.delete()
        # изменение добавленной заявки. меняем только имя ребёнка
        change_requestion_form_data = {
            'name': 'Mary',
            'child_last_name': 'Jordison',
            'sex': 'Ж',
            'birth_date': '07.06.2014',
            'admission_date': '01.01.2014',
            'birthplace': 'Chelyabinsk',
            'kinship_type': 1,
            'areas': '1',
            'location': 'POINT (60.115814208984375 55.051432600719835)',
            'pref_sadiks': [str(kgs[0].id)],
        }
        create_response = self.client.post(
            reverse('account_requestion_info', args=(created_requestion.id,)),
            change_requestion_form_data, follow=True)
        self.assertEqual(create_response.status_code, 200)
        self.assertRedirects(
            create_response,
            reverse('account_requestion_info', args=(created_requestion.id,)))
        # проверяем изменение данных заявки
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.name, 'Mary')
        self.assertEqual(requestion.child_last_name, 'Jordison')
        self.assertEqual(requestion.sex, u'Ж')
        self.assertEqual(requestion.admission_date, datetime.date(2014, 1, 1))
        self.assertEqual(requestion.birthplace, 'Chelyabinsk')
        self.assertEqual(requestion.kinship, u'мать')
        # проверка логов
        logs = Logger.objects.filter(
            action_flag=ACCOUNT_CHANGE_REQUESTION).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertIn('Mary', log_message)
        self.assertNotIn('Jordison', log_message)
        self.assertNotIn(u'Женский', log_message)
        self.assertNotIn('Chelyabinsk', log_message)
        self.assertNotIn(u'мать', log_message)
        last_log.delete()
        # попытка добавить заявку без указания степени родства заявителя
        response = self.client.get(reverse('requestion_add_by_user'))
        token = response.context['form']['token'].value()
        requestion_form_data.update({'token': token, 'kinship_type': 0})
        response = self.client.post(
            reverse('requestion_add_by_user'), requestion_form_data)
        self.assertEqual(response.status_code, 200)
        # теперь с указанием иной степени родства
        response = self.client.get(reverse('requestion_add_by_user'))
        token = response.context['form']['token'].value()
        requestion_form_data.update({'token': token, 'kinship': 'grandfather'})
        response = self.client.post(
            reverse('requestion_add_by_user'),
            requestion_form_data, follow=True)
        self.assertIn('requestion', response.context)
        created_requestion = response.context['requestion']
        requestion_id = created_requestion.id
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response,
            reverse('account_requestion_info', args=(requestion_id,)))
        # проверка данных
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.kinship, 'grandfather')
        # проверка логов
        logs = Logger.objects.filter(
            action_flag=REQUESTION_ADD_BY_REQUESTER).order_by('-datetime')
        self.assertTrue(logs.exists())
        last_log = logs[0]
        account_logs = last_log.loggermessage_set.filter(level=ACCOUNT_LOG)
        self.assertEqual(len(account_logs), 1)
        log_message = account_logs[0].message
        self.assertNotIn(u'мать', log_message)
        self.assertIn('grandfather', log_message)
        last_log.delete()
        # добавление заявки оператором
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
        response = self.client.post(
            reverse('operator_requestion_add', args=(profile.id,)),
            requestion_form_data, follow=True)
        self.assertIn('requestion', response.context)
        created_requestion = response.context['requestion']
        requestion_id = created_requestion.id
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response,
            reverse('operator_requestion_info', args=(requestion_id,)))
        # проверяем сохранение заявки
        requestion = Requestion.objects.get(id=requestion_id)
        self.assertEqual(requestion.name, 'Ann')
        self.assertEqual(requestion.child_last_name, 'Jordison')
        self.assertEqual(requestion.sex, u'Ж')
        self.assertEqual(requestion.admission_date, datetime.date(2014, 1, 1))
        self.assertEqual(requestion.birth_date, datetime.date(2014, 6, 7))
        self.assertEqual(requestion.birthplace, 'Chelyabinsk')
        self.assertEqual(requestion.kinship, 'grandfather')
        evidience_document = requestion.evidience_documents()[0]
        self.assertEqual(evidience_document.document_number, u'II-ИВ 123321')
        # проверка логов
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
        self.assertIn('grandfather', log_message)
        last_log.delete()
        settings.TEST_MODE = False
