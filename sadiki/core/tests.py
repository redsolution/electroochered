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
        Area.objects.create(name='test', ocato='123456')  # , address=address)
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

    def test_distribution(self):
        management.call_command('generate_sadiks', 10)
        management.call_command('generate_requestions', 200,
                                distribute_in_any_sadik=True)
        Requestion.objects.all().update(status=STATUS_REQUESTER)
        # Requestion.objects.all().update(cast=3)
        current_datetime = datetime.date.today()
        current_distribution_year = get_current_distribution_year()
        for age_group in AgeGroup.objects.all():
            group_min_birth_date = age_group.min_birth_date()
            group_max_birth_date = age_group.max_birth_date()
            for sadik in Sadik.objects.all():
                SadikGroup.objects.create(free_places=10,
                                          capacity=10, age_group=age_group, sadik=sadik,
                                          year=current_distribution_year,
                                          min_birth_date=group_min_birth_date,
                                          max_birth_date=group_max_birth_date)
        # группа заявок с датой распределения преывшающей текущую
        # они не должны быть распределены
        requestions_admission_date_ids = list(Requestion.objects.all(
        ).order_by('?')[:30].values_list('id', flat=True))
        admission_date = current_datetime.replace(year=current_datetime.year + 1)
        Requestion.objects.filter(
            id__in=requestions_admission_date_ids).update(admission_date=admission_date)
        # добавим новые ДОУ без мест и заявки желающие распределиться только
        # в эти ДОУ
        existing_sadiks_ids = list(Sadik.objects.all().values_list(
            'id', flat=True))
        management.call_command('generate_sadiks', 5)
        new_sadiks = list(Sadik.objects.exclude(id__in=existing_sadiks_ids))
        requestions_pref_sadiks_ids = list(Requestion.objects.exclude(
            id__in=requestions_admission_date_ids).order_by('?')[:30].values_list(
            'id', flat=True))
        for requestion in Requestion.objects.filter(
                id__in=requestions_pref_sadiks_ids):
            requestion.pref_sadiks = new_sadiks
            requestion.distribute_in_any_sadik = False
            requestion.save()
        requestions_area_distribution_ids = list(Requestion.objects.exclude(
            id__in=requestions_admission_date_ids + requestions_pref_sadiks_ids
        )[:30].values_list('id', flat=True))
        Requestion.objects.filter(id__in=requestions_area_distribution_ids
        ).update(distribute_in_any_sadik=True)
        for requestion in Requestion.objects.filter(
                id__in=requestions_area_distribution_ids):
            requestion.areas = (random.choice(Area.objects.all()),)
            requestion.pref_sadiks = []
        client = Client()
        client.login(username=self.operator.username, password="password")
        client.post(reverse('distribution_init'), data={'confirmation': 'yes'},
                    follow=True)
        decision_manager = DecisionManager()
        last_distributed_requestion = None
        queue_info = decision_manager.queue_info()
        total = 0
        while queue_info['free_places'] and queue_info['queue']:
            requestion = queue_info['current_requestion']
            print 'distributing requestion', requestion.id
            if last_distributed_requestion:
                self.assertEqual(last_distributed_requestion,
                                 queue_info['last_distributed_requestion'], )
            sadiks_for_requestion_dict = decision_manager.sadiks_for_requestion(
                requestion)
            sadiks_for_requestion = sadiks_for_requestion_dict['pref_sadiks'] or \
                                    sadiks_for_requestion_dict['any_sadiks']
            sadik = sadiks_for_requestion[0]
            if requestion.cast == 1:
                response = client.post(
                    reverse('decision_manager'),
                    data={
                        'sadik': sadik.id,
                        'requestion_id': requestion.id,
                        'accept_location': True}
                )
            else:
                response = client.post(reverse('decision_manager'),
                            data={'sadik': sadik.id, 'requestion_id': requestion.id})
            if response.status_code == 302:
                last_distributed_requestion = requestion
                total += 1
            queue_info = decision_manager.queue_info()
        print total

        # проверяем,что заявки с ЖДП, превышающим текущую дату и желающие зачислиться
        # в ДОУ без мест не распределены
        requestions_not_decision_ids = list(requestions_pref_sadiks_ids) + \
                                       list(requestions_admission_date_ids)
        self.assertEqual(
            Requestion.objects.filter(id__in=requestions_not_decision_ids).filter(
                status=STATUS_DECISION).count(), 0)

        # проверяем, что заявка была зачислена в свою возрастную группу
        for requestion in Requestion.objects.filter(status=STATUS_DECISION):
            self.assertIn(requestion.distributed_in_vacancy.sadik_group.age_group,
                          requestion.age_groups())

        # проверяем, что заявки, которые указали возможность зачисления в любой ДОУ
        # были зачислены в нужную территориальную область
        for requestion in Requestion.objects.filter(
                id__in=requestions_area_distribution_ids):
            # проверяем, что заявка попадает в какую-нибудь возрастную группу и
            # может быть распределена
            if requestion.age_groups():
                self.assertEqual(requestion.areas.all()[0],
                                 requestion.distributed_in_vacancy.sadik_group.sadik.area)