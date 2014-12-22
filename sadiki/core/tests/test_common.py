# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.core import management
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import Client
from django.test.testcases import TestCase
from sadiki.account.urls import urlpatterns as account_patterns
from sadiki.anonym.urls import urlpatterns as anonym_patterns
from sadiki.authorisation.urls import urlpatterns as auth_patterns
from sadiki.core.models import Requestion, Profile, STATUS_REQUESTER, Address, \
    Area, Sadik, REQUESTION_IDENTITY, AgeGroup, SadikGroup, STATUS_DECISION, \
    Preference, PREFERENCE_IMPORT_FINISHED
from sadiki.core.permissions import OPERATOR_GROUP_NAME, \
    SADIK_OPERATOR_GROUP_NAME, DISTRIBUTOR_GROUP_NAME, SUPERVISOR_GROUP_NAME
from sadiki.core.utils import get_current_distribution_year
from sadiki.distribution.urls import urlpatterns as distribution_patterns
from sadiki.distribution.views import DecisionManager
from sadiki.logger.urls import urlpatterns as logger_patterns
from sadiki.operator.urls import urlpatterns as operator_patterns
from sadiki.statistics.urls import urlpatterns as statictics_patterns
from sadiki.supervisor.urls import urlpatterns as supervisor_patterns
import datetime
import random


class TestAll(TestCase):
    fixtures = ['sadiki/core/fixtures/test_initial.json', ]

    def setUp(self):
        management.call_command('update_initial_data')
        address = Address.objects.create(postindex=123456, street=u'ул.Кирова',
                                         building_number=17, )
        # Area.objects.create(name='test', ocato='123456')  # , address=address)
        #        Requestion.objects.all().update(status=STATUS_REQUESTER)
        self.operator = User(username='operator')
        self.operator.set_password("password")
        self.operator.save()
        Profile.objects.create(user=self.operator)
        operator_group = Group.objects.get(name=OPERATOR_GROUP_NAME)
        sadik_operator_group = Group.objects.get(name=SADIK_OPERATOR_GROUP_NAME)
        distributor_group = Group.objects.get(name=DISTRIBUTOR_GROUP_NAME)
        self.operator.groups = (operator_group, sadik_operator_group, distributor_group)
        self.supervisor = User(username="supervisor")
        self.supervisor.set_password("password")
        self.supervisor.save()
        Profile.objects.create(user=self.supervisor)
        supervisor_group = Group.objects.get(name=SUPERVISOR_GROUP_NAME)
        self.supervisor.groups = (supervisor_group,)

    def test_get_requests(self):
        u"""Test GET requests for url"""
        management.call_command('generate_sadiks', 1)
        management.call_command('generate_requestions', 2,
                                distribute_in_any_sadik=True)
        client = Client()

        def urls_for_patterns(patterns, kwargs=None):
            exclude_patterns = ('operator_generate_blank',
                                'account_generate_blank',
                                'operator_requestion_set_identity_document',
                                'start_distribution_year')
            if kwargs is None:
                kwargs = {}
            urls = []
            for pattern in patterns:
                if pattern.name not in exclude_patterns:
                    try:
                        urls.append(reverse(pattern.name, kwargs=kwargs))
                    except NoReverseMatch:
                        pass
            return urls

        # интерфейс анонимного пользователя
        for url in urls_for_patterns(anonym_patterns):
            if not Preference.objects.filter(key=PREFERENCE_IMPORT_FINISHED).exists():
                Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)
            r_code = client.get(url).status_code
            self.assertEqual(r_code, 200,
                             "URL {} for anonymous returns {} instead of 200".format(url, r_code))

        # интерфейс оператора
        client.login(username=self.operator.username, password="password")
        requestion = Requestion.objects.all()[0]
        sadik = Sadik.objects.all()[0]
        operator_urls = urls_for_patterns(operator_patterns) + \
                        urls_for_patterns(operator_patterns,
                                          kwargs={'requestion_id': requestion.id}) + \
                        urls_for_patterns(operator_patterns,
                                          kwargs={'sadik_id': sadik.id})
        for url in operator_urls:
            status_code = client.get(url).status_code
            # некоторые url разрешают только post-запросы
            if url == '/operator/request/{}/change_location/'.format(requestion.id):
                self.assertEqual(status_code, 405,
                                 "URL {} for operator returns {} instead of 405".format(url, status_code))
            else:
                self.assertEqual(status_code, 200,
                                 "URL {} for operator returns {} instead of 200".format(url, status_code))

        # проверяем интерфейс оператора анонимом
        client.logout()
        for url in operator_urls:
            self.assertEqual(client.get(url).status_code, 403, url)

        # проверяем возможность задать идентифицирующий документ заявки
        # заявка без удостоверяющего документа
        requestion = Requestion.objects.all()[1]
        requestion.evidience_documents().get(
            template__destination=REQUESTION_IDENTITY).delete()
        url = reverse('operator_requestion_set_identity_document',
                      kwargs={'requestion_id': requestion.id})
        status_code = client.post(url).status_code
        self.assertEqual(status_code, 403,
                         "URL {} for anonymous returns {} instead of 403".format(url, status_code))
        client.login(username=self.operator.username, password="password")
        status_code = client.post(url).status_code
        self.assertEqual(status_code, 403,
                         "URL {} for operator returns {} instead of 403".format(url, status_code))

        # проверяем, что работают отчеты
        url = "%s?type=registration" % reverse('operator_generate_blank',
                                               kwargs={"requestion_id": requestion.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        client.logout()
        response = client.get(url)
        self.assertEqual(response.status_code, 403)

        # интерфейс суперпользователя
        supervisor_urls = urls_for_patterns(supervisor_patterns) + \
                          urls_for_patterns(supervisor_patterns,
                                            kwargs={'requestion_id': requestion.id})
        # для супервайзера
        client.login(username=self.supervisor.username, password="password")
        for url in supervisor_urls:
            response = client.get(url)
            self.assertEqual(response.status_code, 200, url)
        # для оператора
        client.login(username=self.operator.username, password="password")
        for url in supervisor_urls:
            self.assertEqual(client.get(url).status_code, 403, url)
        # для анонимного пользователя
        client.logout()
        for url in supervisor_urls:
            self.assertEqual(client.get(url).status_code, 403, url)
            #        TODO: реализовать проверку начала нового года
