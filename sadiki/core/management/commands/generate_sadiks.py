# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.utils import simplejson
from sadiki.core.models import Area, Sadik, Address, AgeGroup
from django.conf import settings
from os.path import join
from random import choice, randint
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
    help = "Generates sadiks"
    args = ['num',]

    def handle(self, *args, **options):
        if args:
            names = simplejson.loads(open(join(settings.PROJECT_DIR, 'sadiki','core', 'fixtures', 'names.json'), 'r').read())

            for i in progressbar(xrange(int(args[0]))):
                # create sadik
                address, created = Address.objects.get_or_create(
                    postindex=123456,
                    street=u'ул.Кирова',
                    building_number=17,)

                sadik = Sadik.objects.create(
                    area=Area.objects.all().order_by('?')[0],
                    name=u"МДОУ №%d" % i,
                    short_name=u"МДОУ №%d" % i,
                    number=i,
                    address=address,
                    email=u"sadik_%d@example.com" % i,
                    site=u"example.com",
                    head_name = u"%s %s %s" % (choice(names['last']), choice(names['first']), choice(names['patronymic'])),
                    phone='+7351%07d' % randint(0,999999),
                    cast=u' ',
                )
                sadik.age_groups = AgeGroup.objects.all()
        else:
            raise CommandError('Required argument num')
