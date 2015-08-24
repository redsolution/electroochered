# -*- coding: utf-8 -*-
import os
import datetime
from django.test import TestCase
from django.core import management
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.models import Permission, Group, User

from sadiki.core.models import Requestion, Profile, BenefitCategory, Benefit, \
    Sadik, REQUESTION_TYPE_IMPORTED, REQUESTION_TYPE_CORRECTED, \
    REQUESTION_TYPE_NORMAL, STATUS_REJECTED, SadikGroup, Address, \
    STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REQUESTER
from sadiki.core.tests import utils as test_utils


class RequestionTestCase(TestCase):
    fixtures = ['sadiki/core/fixtures/test_initial.json',]

    @classmethod
    def setUpClass(cls):
        for fixture_filename in cls.fixtures:
            fixture_file = os.path.join(settings.PROJECT_DIR, fixture_filename)
            management.call_command('loaddata', fixture_file)
        test_utils.create_objects(test_utils.create_area, 5)
        management.call_command('generate_sadiks', 10)

    @classmethod
    def tearDownClass(cls):
        Permission.objects.all().delete()
        Group.objects.all().delete()
        BenefitCategory.objects.all().delete()
        Address.objects.all().delete()

    def setUp(self):
        self.requestion = test_utils.create_requestion(name='Ann')

    def tearDown(self):
        Requestion.objects.all().delete()
        SadikGroup.objects.all().delete()

    def test_requestion_creation(self):
        self.assertEqual(self.requestion.name, 'Ann')
        self.assertTrue(self.requestion.all_fields_filled())
        self.requestion.sex = u'М'
        self.assertTrue(self.requestion.all_fields_filled())
        self.assertEqual(self.requestion.cast, REQUESTION_TYPE_NORMAL)

    def test_location_not_verified(self):
        self.requestion.cast = REQUESTION_TYPE_IMPORTED
        self.assertTrue(self.requestion.needs_location_confirmation)
        self.assertTrue(self.requestion.location_not_verified)

        self.requestion.cast = REQUESTION_TYPE_CORRECTED
        self.assertFalse(self.requestion.needs_location_confirmation)
        self.assertFalse(self.requestion.location_not_verified)

        self.requestion.cast = REQUESTION_TYPE_IMPORTED
        self.requestion.location = None
        self.assertTrue(self.requestion.location_not_verified)

    def test_set_location(self):
        self.requestion.set_location([1.5, 4.8])
        self.assertEqual(self.requestion.location[0], 1.5)
        self.assertEqual(self.requestion.location[1], 4.8)

    def test_clean_no_birth_greater_today(self):
        self.requestion.birth_date = datetime.date.today() + datetime.timedelta(
            days=1)
        self.assertRaises(ValidationError, self.requestion.clean)

    def test_position_in_queue(self):
        # одна заявка, должна быть первой
        self.assertEqual(self.requestion.position_in_queue(), 1)

        # делаем заявку с более высоким приоритетом,
        # смещаем первую на второе место
        benefit_category_high = BenefitCategory.objects.get(priority=1)
        high_priority = test_utils.create_requestion(
            benefit_category=benefit_category_high)
        self.assertEqual(self.requestion.position_in_queue(), 2)

        # добавим еще одну заявку, без привелегий
        last_req = test_utils.create_requestion()
        self.assertEqual(last_req.position_in_queue(), 3)
        # убираем из очереди приоритетную
        high_priority.status = STATUS_REJECTED
        high_priority.save()
        self.assertEqual(last_req.position_in_queue(), 2)

    def test_all_group_methods(self):
        kidgdn = Sadik.objects.all()[0]
        test_requestion = test_utils.create_requestion(
            admission_date=datetime.date.today() + datetime.timedelta(days=365),
            birth_date=datetime.date.today()-datetime.timedelta(days=365)
        )
        test_requestion.areas.add(kidgdn.area)
        test_requestion.save()
        test_utils.create_age_groups_for_sadik(kidgdn)

        groups = test_requestion.get_sadiks_groups()
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].sadik, kidgdn)
        self.assertEqual(groups[0].age_group.id, 2)

        groups_for_kidgdn = test_requestion.get_sadik_groups(kidgdn)
        self.assertEqual(len(groups_for_kidgdn), 1)
        self.assertEqual(groups_for_kidgdn[0], groups[0])

        age_groups = test_requestion.age_groups()
        self.assertEqual(len(age_groups), 1)
        self.assertEqual(age_groups[0].id, 2)
        self.assertEqual(groups[0].age_group, age_groups[0])

        # слишком маленький ребенок, никуда не распределяем
        small_requestion = test_utils.create_requestion(
            admission_date=datetime.date(datetime.date.today().year, 1, 1),
            birth_date=datetime.date.today()-datetime.timedelta(days=1)
        )
        small_requestion.areas.add(kidgdn.area)
        groups_small = small_requestion.get_sadiks_groups()
        self.assertEqual(len(groups_small), 0)

    def test_days_for_appeal(self):
        self.requestion.status_change_datetime = datetime.datetime.now() - (
            datetime.timedelta(days=settings.APPEAL_DAYS + 1))
        self.requestion.save()
        self.assertEqual(self.requestion.days_for_appeal(), 0)

        self.requestion.status_change_datetime = datetime.datetime.now() - (
            datetime.timedelta(days=settings.APPEAL_DAYS - 1))
        self.requestion.save()
        self.assertEqual(self.requestion.days_for_appeal(), 1)

    def test_status_change(self):
        self.assertIsNone(self.requestion.previous_status)
        self.assertEqual(self.requestion.status, STATUS_REQUESTER_NOT_CONFIRMED)

        self.requestion.change_status(STATUS_REQUESTER)
        self.assertEqual(self.requestion.status, STATUS_REQUESTER)
        self.assertEqual(
            self.requestion.previous_status, STATUS_REQUESTER_NOT_CONFIRMED)


class ProfileTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='requester')
        self.profile = Profile.objects.create(user=self.user)

    def test_save_method(self):
        self.assertFalse(self.user.first_name)
        self.assertFalse(self.user.last_name)
        self.assertFalse(self.profile.middle_name)
        self.profile.first_name = 'Vasya'
        self.profile.last_name = 'Ivanov'
        self.profile.middle_name = 'Petrovich'
        self.profile.save()
        self.assertEqual(self.user.first_name, 'Vasya')
        self.assertEqual(self.user.last_name, 'Ivanov')
        self.assertEqual(self.profile.middle_name, 'Petrovich')

    def test_social_auth_methods(self):
        self.profile.phone_number = '123456'
        self.profile.skype = '567'
        self.profile.save()
        self.assertFalse(self.profile.first_name)
        self.assertEqual(self.profile.phone_number, '123456')
        self.assertEqual(self.profile.skype, '567')
        self.assertFalse(self.profile.mobile_number)
        vk_data = {'first_name': 'Vasya', 'home_phone': '555', 'skype': '123'}
        self.profile.update_vkontakte_data(vk_data)
        # Обновляем имя, телефон и скайп. Скайп перезаписывается,
        # а телефон сохраняется в mobile_number, так как phone_number занят
        self.assertEqual(self.profile.first_name, 'Vasya')
        self.assertEqual(self.profile.phone_number, '123456')
        self.assertEqual(self.profile.mobile_number, '555')
        self.assertEqual(self.profile.skype, '123')

        self.profile.first_name = ''
        self.profile.middle_name = 'Ivanovich'
        self.profile.save()
        self.assertFalse(self.profile.first_name)
        self.assertEqual(self.profile.middle_name, 'Ivanovich')
        vk_data = {'first_name': 'Vasya', 'home_phone': '777', 'skype': '888'}
        self.profile.update_vkontakte_data(vk_data)
        # Если отчество уже заполнено, имя из ВК игнорируется
        # Также игнорируется телефон, т.к. оба поля уже заполнены.
        self.assertFalse(self.profile.first_name)
        self.assertEqual(self.profile.phone_number, '123456')
        self.assertEqual(self.profile.mobile_number, '555')
        self.assertEqual(self.profile.skype, '888')

        # Тест метода очистки данных. Удаляется только скайп
        self.profile.first_name = 'Vasya'
        self.profile.save()
        self.assertEqual(self.profile.first_name, 'Vasya')
        self.profile.social_auth_clean_data()
        self.assertEqual(self.profile.first_name, 'Vasya')
        self.assertEqual(self.profile.phone_number, '123456')
        self.assertEqual(self.profile.mobile_number, '555')
        self.assertFalse(self.profile.skype)

    def tearDown(self):
        Profile.objects.all().delete()
        User.objects.all().delete()


class BenefitTestCase(TestCase):
    fixtures = ['sadiki/core/fixtures/test_initial.json', ]

    @classmethod
    def setUpClass(cls):
        for fixture_filename in cls.fixtures:
            fixture_file = os.path.join(settings.PROJECT_DIR, fixture_filename)
            management.call_command('loaddata', fixture_file)
        management.call_command('update_initial_data')

    @classmethod
    def tearDownClass(cls):
        BenefitCategory.objects.all().delete()
        Benefit.objects.all().delete()

    def tearDown(self):
        Benefit.objects.all().delete()

    def test_disabled(self):
        # все заявки изначально включены.
        self.assertItemsEqual(Benefit.objects.all(),
                              Benefit.enabled.all())

        # Отключаем одну льготу.  Проверяем количество всех. 
        # Проверяем количество включеных и убеждаемся в том, что там ее нет.
        all_count = Benefit.objects.count()
        enabled_count = Benefit.enabled.count()
        benefit = test_utils.disable_random_benefit()
        self.assertEqual(Benefit.enabled.count(), 
                         enabled_count - 1)
        self.assertEqual(Benefit.objects.count(), all_count)
        self.assertNotIn(benefit, Benefit.enabled.all())

        # Отключаем все заявки. 
        # Проверяем, что количество включеных = 0
        # Проверяем, чтобы количество всех заявок не изменилось 
        Benefit.objects.all().update(disabled=True)
        self.assertEqual(Benefit.enabled.count(), 0)
        self.assertNotEqual(Benefit.objects.count(), 0)
