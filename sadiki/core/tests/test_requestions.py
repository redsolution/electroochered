# -*- coding: utf-8 -*-
import random
import string
import datetime
from django.utils import unittest
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.core import management

from sadiki.core.models import Requestion, Area, BenefitCategory, \
    Profile


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


def create_requestion():
    birth_date = datetime.date.today()-datetime.timedelta(
        days=random.randint(0, settings.MAX_CHILD_AGE*12*30))

    defaults = {
        'admission_date': get_admission_date(),
        'distribute_in_any_sadik': True,
        'birth_date': birth_date,
        'profile': create_profile()
    }
    r = Requestion.objects.create(**defaults)
    r.areas.add(create_area())
    return r


class SimpleTestCase(unittest.TestCase):
    fixtures = ['sadiki/core/fixtures/test_initial.json', ]

    def test_add(self):
        self.assertEqual(2+2, 4)

    def test_requestion_creation(self):
        management.call_command('update_initial_data')
        # benefit_cat = create_benefit_category()
        r1 = create_requestion()