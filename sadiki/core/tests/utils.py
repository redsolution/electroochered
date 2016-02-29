# -*- coding: utf-8 -*-
import random
import string
import datetime
import json
import os.path

from django.contrib.gis.geos import point
from django.conf import settings
from django.contrib.auth.models import User, Permission
from sadiki.core import utils

from sadiki.core.models import Requestion, Area, BenefitCategory, \
    Profile, AgeGroup, SadikGroup, Benefit, EvidienceDocumentTemplate, \
    EvidienceDocument, REQUESTION_IDENTITY


def disable_random_benefit():
    id_ = random.randrange(Benefit.objects.count())
    benefit = Benefit.objects.all()[id_]
    benefit.disabled = True
    benefit.save()
    return benefit


def get_random_string(length, only_letters=False, only_digits=False):
    if only_digits:
        return ''.join([random.choice(string.digits) for _ in xrange(length)])
    if only_letters:
        return ''.join([random.choice(string.ascii_letters) for _ in xrange(length)])
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in xrange(length)])


def create_objects(f, number, **kwargs):
    for i in range(number):
        obj = f(**kwargs)
    return obj


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
    names = json.loads(
        open(os.path.join(
            settings.PROJECT_DIR, 'sadiki', 'core', 'fixtures', 'names.json'),
            'r').read())
    default_birth_date = datetime.date.today()-datetime.timedelta(
        days=random.randint(0, settings.MAX_CHILD_AGE*12*30))

    defaults = {
        'name': random.choice(names['first']),
        'child_last_name': random.choice(names['last']),
        'sex': random.choice([u'М', u'Ж']),
        'admission_date': get_admission_date(),
        'distribute_in_any_sadik': True,
        'birth_date': default_birth_date,
        'birthplace': 'Chelyabinsk',
        'kinship_type': random.choice([0, 1, 2]),
        'kinship': get_random_string(10),
        'profile': create_profile(),
        'location_properties': 'челябинск',
        'location': point.Point(random.choice([1, 2, 3, 4]),
                                random.choice([1, 2, 3, 4])),
    }
    defaults.update(kwargs)

    requestion = Requestion.objects.create(**defaults)
    if Area.objects.exists():
        requestion.areas.add(Area.objects.all().order_by('?')[0])
    else:
        requestion.areas.add(create_area())
    requestion_document = EvidienceDocument.objects.create(
        content_object=requestion,
        template=EvidienceDocumentTemplate.objects.filter(
            destination=REQUESTION_IDENTITY)[0],
        document_number='II-ИВ %06d' % random.randint(0, 99999)
    )

    return requestion


def create_age_groups_for_sadik(kidgdn):
    current_distribution_year = utils.get_current_distribution_year()
    for age_group in AgeGroup.objects.all():
        group_min_birth_date = age_group.min_birth_date()
        group_max_birth_date = age_group.max_birth_date()
        SadikGroup.objects.create(
            free_places=2,
            capacity=2,
            age_group=age_group, sadik=kidgdn,
            year=current_distribution_year,
            min_birth_date=group_min_birth_date,
            max_birth_date=group_max_birth_date)
