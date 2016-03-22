# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.conf import settings
from django.core import management
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse

from sadiki.core.models import (
    Profile, BenefitCategory, Requestion, Sadik,
    SadikGroup, Preference, PREFERENCE_IMPORT_FINISHED, Address,
    PersonalDocument)
from sadiki.core.permissions import OPERATOR_GROUP_NAME, SUPERVISOR_GROUP_NAME, \
    SADIK_OPERATOR_GROUP_NAME, DISTRIBUTOR_GROUP_NAME
from sadiki.core.tests import utils as test_utils


class OperatorViewsTest(TestCase):
    fixtures = [
        'sadiki/core/fixtures/test_initial.json',
        'sadiki/core/fixtures/perms.json',
        'sadiki/core/fixtures/groups.json',
        ]

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

    def test_requestion_add(self):
        u"""
        Проверяем корректрость работы ключа token, хранящегося в сессии
        пользователя.
        """
        settings.TEST_MODE = True

        management.call_command('generate_sadiks', 10)
        kgs = Sadik.objects.all()
        url = reverse('anonym_registration')
        admission_date = datetime.date.today() + datetime.timedelta(days=3)
        form_data = {
            'core-evidiencedocument-content_type-object_id-TOTAL_FORMS': '1',
            'core-evidiencedocument-content_type-object_id-INITIAL_FORMS': '0',
            'core-evidiencedocument-content_type-object_id-MAX_NUM_FORMS':
                '1000',
        }
        self.assertTrue(self.client.login(username=self.operator.username,
                                          password='password'))
        # до посещения страницы с формой, токена нет
        self.assertIsNone(self.client.session.get('token', None))
        # заявка не сохраняется, редирект на страницу добавления заявки
        create_response = self.client.post(
            url, {
                'name': 'Ann',
                'child_last_name': 'Jordison',
                'sex': 'Ж',
                'birth_date': '07.06.2014',
                'admission_date': admission_date.strftime('%d.%m.%Y'),
                'template': '2',
                'document_number': 'II-ИВ 016809',
                'birthplace': 'Chelyabinsk',
                'kinship_type': 1,
                'areas': '1',
                'location': 'POINT (60.115814208984375 55.051432600719835)',
                'pref_sadiks': [str(kgs[0].id), str(kgs[1].id)],
            })
        self.assertEqual(create_response.status_code, 302)
        self.assertRedirects(create_response, url)
        self.assertIsNotNone(self.client.session.get('token'))

        # зашли на страницу с формой, токен появился
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        token = response.context['form']['token'].value()
        self.assertIsNotNone(self.client.session.get('token'))
        self.assertIsNone(self.client.session['token'][token])

        # успешный post, создается заявка, токен удаляется
        form_data.update(
            {'name': 'Ann',
             'child_last_name': 'Jordison',
             'sex': 'Ж',
             'birth_date': '07.06.2014',
             'admission_date': admission_date.strftime('%d.%m.%Y'),
             'template': '2',
             'document_number': 'II-ИВ 016809',
             'birthplace': 'Chelyabinsk',
             'kinship_type': 1,
             'areas': '1',
             'location': 'POINT (60.115814208984375 55.051432600719835)',
             'token': token,
             'pref_sadiks': [str(kgs[0].id), str(kgs[1].id)], }
        )
        create_response = self.client.post(url, form_data)
        requestion = create_response.context['requestion']
        self.assertEqual(create_response.status_code, 302)
        self.assertRedirects(
            create_response,
            reverse('operator_requestion_info', args=(requestion.id,)))
        self.assertIsNotNone(self.client.session.get('token', None))
        self.assertEqual(self.client.session['token'][token], requestion.id)

        # пробуем с таким же токеном еще раз, перенаправляет на
        # заявку c id, хранящемся в сессии по токену, если такая имеется
        form_data.update(
            {'name': 'Mary',
             'birth_date': '06.06.2014',
             'template': '2',
             'document_number': 'II-ИВ 016808',
             'areas': '2',
             'token': token, }
        )
        create_response = self.client.post(url, form_data)
        self.assertEqual(create_response.status_code, 302)
        token_req_num = self.client.session['token'][token]
        self.assertRedirects(
            create_response,
            reverse('operator_requestion_info', args=(token_req_num,)))
        self.assertIsNotNone(self.client.session.get('token'))

        # пробуем с неверным токеном еще раз, перенаправляет на
        # страницу добавления заявки
        form_data.update(
            {'name': 'Mary',
             'birth_date': '06.06.2014',
             'template': '2',
             'document_number': 'II-ИВ 016808',
             'areas': '2',
             'token': 'some-wrong-token', }
        )
        create_response = self.client.post(url, form_data)
        self.assertEqual(create_response.status_code, 302)
        self.assertRedirects(create_response, url)
        self.assertIsNotNone(self.client.session.get('token'))
        self.assertEqual(len(self.client.session['token']), 3)

        settings.TEST_MODE = False

    # тест поиска профилей по имени, пока банальная проверка на status code 200
    def test_profile_search(self):
        permission = Permission.objects.get(codename=u'is_requester')
        user = User.objects.create(username='requester_1')
        user.user_permissions.add(permission)
        profile = Profile.objects.create(user=user)
        profile.first_name = u'Иван'
        profile.save()
        user = User.objects.create(username='requester_2')
        user.user_permissions.add(permission)
        profile = Profile.objects.create(user=user)
        profile.first_name = u'Иван'
        profile.save()
        new_requestion = test_utils.create_requestion(profile=profile)
        user = User.objects.create(username='requester_3')
        user.user_permissions.add(permission)
        profile = Profile.objects.create(user=user)
        profile.first_name = u'Андрей'
        profile.save()

        self.assertTrue(self.client.login(username=self.operator.username,
                                          password='password'))
        old_requestion = test_utils.create_requestion(
            profile=self.requester.profile)
        profile_search_url = reverse('find_profile_for_requestion',
                                     args=(old_requestion.id,))
        # ищем по имени заявителя, которое должно найтись
        search_form_data = {'parent_first_name': u'Иван'}
        response = self.client.post(profile_search_url, search_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'requester_1')
        self.assertContains(response, 'requester_2')
        self.assertNotContains(response, 'requester_3')
        # ищем по несуществующему имени заявителя
        search_form_data = {'parent_first_name': u'Вася'}
        response = self.client.post(profile_search_url, search_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'requester_1')
        self.assertNotContains(response, 'requester_2')
        self.assertNotContains(response, 'requester_3')
        # ищем только по имени User
        search_form_data = {'username': 'requester_2'}
        response = self.client.post(profile_search_url, search_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'requester_1')
        self.assertContains(response, 'requester_2')
        self.assertNotContains(response, 'requester_3')
        # ищем по имени заявителя и имени User одновременно
        search_form_data = {'username': 'requester_3',
                            'parent_first_name': u'Андрей'}
        response = self.client.post(profile_search_url, search_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'requester_1')
        self.assertNotContains(response, 'requester_2')
        self.assertContains(response, 'requester_3')
        # ищем по номеру заявки
        search_form_data = {
            'requestion_number': new_requestion.requestion_number}
        response = self.client.post(profile_search_url, search_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'requester_1')
        self.assertContains(response, 'requester_2')
        self.assertNotContains(response, 'requester_3')

    def test_requestion_search(self):
        today = datetime.date.today()
        date1 = today - datetime.timedelta(days=500)
        date2 = today - datetime.timedelta(days=1000)
        date3 = today - datetime.timedelta(days=800)
        date4 = today - datetime.timedelta(days=1200)
        permission = Permission.objects.get(codename=u'is_requester')
        user = User.objects.create(username='requester_1')
        user.user_permissions.add(permission)
        profile = Profile.objects.create(user=user)
        profile.first_name = u'Иван'
        profile.last_name = u'Иванов'
        profile.save()
        document = PersonalDocument.objects.create(
            profile=profile, series='1234', number='135790')
        requestion1 = test_utils.create_requestion(
            profile=profile, name=u'Серёжа', child_last_name=u'Иванов',
            birth_date=date2)
        requestion1.update_registration_datetime(date1)
        requestion2 = test_utils.create_requestion(
            profile=profile, name=u'Василий', child_last_name=u'Иванов',
            birth_date=date3)
        user = User.objects.create(username='requester_2')
        user.user_permissions.add(permission)
        profile = Profile.objects.create(user=user)
        profile.first_name = u'Андрей'
        profile.last_name = u'Смирнов'
        profile.save()
        requestion3 = test_utils.create_requestion(
            profile=profile, name=u'Саша', child_last_name=u'Смирнова',
            birth_date=date4)
        number1 = requestion1.requestion_number
        number2 = requestion2.requestion_number
        number3 = requestion3.requestion_number

        self.assertTrue(self.client.login(username=self.operator.username,
                                          password='password'))
        post_url = reverse('anonym_requestion_search')
        # поиск по номеру заявки
        post_data = {'requestion_number': requestion2.requestion_number}
        response = self.client.post(post_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, number1)
        self.assertContains(response, number2)
        self.assertNotContains(response, number3)
        # поиск по дате регистрации
        post_data = {'registration_date': today.strftime('%d.%m.%Y')}
        response = self.client.post(post_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, number1)
        self.assertContains(response, number2)
        self.assertContains(response, number3)
        # поиск по данным ребёнка
        post_data = {'child_name': u'Серёжа'}
        response = self.client.post(post_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, number1)
        self.assertNotContains(response, number2)
        self.assertNotContains(response, number3)
        post_data = {'child_name': u'Саша', 'child_last_name': u'Смирнова'}
        response = self.client.post(post_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, number1)
        self.assertNotContains(response, number2)
        self.assertContains(response, number3)
        # поиск по данным заявителя
        post_data = {'requester_first_name': u'Иван',
                     'requester_last_name': u'Иванов'}
        response = self.client.post(post_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, number1)
        self.assertContains(response, number2)
        self.assertNotContains(response, number3)
        # комбинированный поиск: перс. данные заявителя + дата рождения ребёнка
        post_data = {'requester_document_series': '1234',
                     'requester_document_number': '135790',
                     'birth_date': date3.strftime('%d.%m.%Y')}
        response = self.client.post(post_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, number1)
        self.assertContains(response, number2)
        self.assertNotContains(response, number3)
