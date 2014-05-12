# -*- coding: utf-8 -*-
import random
import string
import datetime
from django.contrib.gis.geos import point
from django.utils import unittest
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.core import management
from django.core.exceptions import ValidationError

from sadiki.core.models import Requestion, Area, BenefitCategory, \
    Profile, REQUESTION_TYPE_IMPORTED, REQUESTION_TYPE_CORRECTED, \
    REQUESTION_TYPE_NORMAL


def get_random_string(length, only_letters=False, only_digits=False):
    if only_digits:
        return ''.join([random.choice(string.digits) for _ in xrange(length)])
    if only_letters:
        return ''.join([random.choice(string.ascii_letters) for _ in xrange(length)])
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in xrange(length)])


def create_area(**kwargs):
    defaults = {
        'name': get_random_string(8, only_letters=True),
        'ocato': get_random_string(11, only_digits=True),
    }
    defaults.update(kwargs)
    return Area.objects.create(**defaults)


def create_benefit_category(**kwargs):
    defaults = {
        'name': get_random_string(10),
        'description': get_random_string(50),
        'priority': 0,
    }
    defaults.update(kwargs)
    return BenefitCategory.objects.create(**defaults)


def create_profile(**kwargs):
    permission = Permission.objects.get(codename=u'is_requester')
    user = User.objects.create(
        username='user%15d@mail.ru' % random.randint(0, 99999999999999),
    )
    user.user_permissions.add(permission)
    defaults = {
        'user': user,
        'area': create_area(),
        'first_name': get_random_string(8),
        'email_verified': bool(random.random()*1.6 < 1),
    }
    defaults.update(kwargs)
    return Profile.objects.create(**defaults)


def get_admission_date():
    admission_date = random.randrange(
        datetime.date.today().year,
        datetime.date.today().year + 3
    )
    return datetime.date(admission_date, 1, 1)


def create_requestion(**kwargs):
    birth_date = datetime.date.today()-datetime.timedelta(
        days=random.randint(0, settings.MAX_CHILD_AGE*12*30))

    defaults = {
        'admission_date': get_admission_date(),
        'distribute_in_any_sadik': True,
        'birth_date': birth_date,
        'profile': create_profile(),
        'location_properties': 'челябинск',
        'location': point.Point(random.choice([1, 2, 3, 4]), random.choice([1, 2, 3, 4])),
    }
    defaults.update(kwargs)
    requestion = Requestion.objects.create(**defaults)
    requestion.areas.add(create_area())
    return requestion


class RequestionTestCase(unittest.TestCase):
    fixtures = ['sadiki/core/fixtures/test_initial.json', ]

    @classmethod
    def setUpClass(cls):
        management.call_command('update_initial_data')

    def setUp(self):
        self.requestion = create_requestion(name='Ann')

    def test_requestion_creation(self):
        self.assertEqual(self.requestion.name, 'Ann')
        self.assertFalse(self.requestion.all_fields_filled())
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

    def test_clean(self):
        self.requestion.birth_date = datetime.date.today() + datetime.timedelta(days=1)
        self.assertRaises(ValidationError, self.requestion.clean)
