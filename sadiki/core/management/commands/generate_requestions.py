# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import point
from django.utils import simplejson
from optparse import make_option
from os.path import join
from sadiki.core.models import Requestion, Profile, Area, Sadik, \
    EvidienceDocument, EvidienceDocumentTemplate, PROFILE_IDENTITY, \
    REQUESTION_IDENTITY, Address
import datetime
import random
import sys


def progressbar(it, prefix = "", size = 60):
    count = len(it)
    def _show(_i):
        x = int(size*_i/count)
        sys.stdout.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), _i, count))
        sys.stdout.flush()

    _show(0)
    for i, item in enumerate(it):
        yield item
        _show(i+1)
    sys.stdout.write("\n")
    sys.stdout.flush()


class Command(BaseCommand):
    help = "Generates num random requestions"
    args = ['num',]
    option_list = BaseCommand.option_list + (
        make_option('--distribute_in_any_sadik', default=False, 
            action="store_true"),
        make_option('--verbose', action='store_false', default=False,
            dest='verbose'),)

    def handle(self, *args, **options):
        random.seed()
        if args:
            names = simplejson.loads(open(join(settings.PROJECT_DIR, 'sadiki', 'core', 'fixtures', 'names.json'), 'r').read())
            max_sadiks = 5
            permission = Permission.objects.get(codename=u'is_requester')
            
            if options['verbose']:
                numbers = progressbar(xrange(int(args[0])))
            else:
                numbers = xrange(int(args[0]))
            for i in numbers:
                # create user and profile
                user = User.objects.create(
                    username='user%15d@mail.ru' % random.randint(0,99999999999999),
                )
                user.user_permissions.add(permission)

                if Area.objects.exists():
                    area = Area.objects.order_by('?')[0]
                else:
                    area = None

                address, created = Address.objects.get_or_create(
                    postindex=123456,
                    street=u'ул.Кирова',
                    building_number=17,)

                profile = Profile.objects.create(
                    user=user,
                    area=area,
                    first_name=random.choice(names['first']),
                    email_verified=bool(random.random()*1.6 < 1),
                    phone_number='+7351%07d' % random.randint(0,999999),
                    mobile_number='+7919%07d' % random.randint(0,999999),
                )
                
                birth_date = datetime.date.today()-datetime.timedelta(
                    days=random.randint(0, settings.MAX_CHILD_AGE*12*30))
                requestion = Requestion.objects.create(
                    profile=profile,
                    birth_date=birth_date,
                    name=random.choice(names['first']),
                    sex=random.choice([u'М', u'Ж']),
                    cast=random.choice([0, 1, 2, 3]),
                    status=random.choice([3, 4]),
                    distribute_in_any_sadik=True,
                    location_properties='челябинск',
                    location=point.Point(random.choice([1, 2, 3, 4]), random.choice([1, 2, 3, 4]))
                )
                
                requestion.areas.add(area)
                if requestion.distribute_in_any_sadik:
                    min_sadiks = 0
                else:
                    min_sadiks = 1

                for sadik in Sadik.objects.filter(area=requestion.areas.all()[0]).order_by('?')[:random.randint(min_sadiks, max_sadiks)]:
                    requestion.pref_sadiks.add(sadik)

                profile_document = EvidienceDocument.objects.create(
                    content_object=profile,
                    template=EvidienceDocumentTemplate.objects.filter(destination=PROFILE_IDENTITY)[0],
                    document_number='7505 %06d' % random.randint(0,99999)
                )

                requestion_document = EvidienceDocument.objects.create(
                    content_object=requestion,
                    template=EvidienceDocumentTemplate.objects.filter(destination=REQUESTION_IDENTITY)[0],
                    document_number='II-ИВ %06d' % random.randint(0,99999)
                )

        else:
            raise CommandError('Required argument num')
