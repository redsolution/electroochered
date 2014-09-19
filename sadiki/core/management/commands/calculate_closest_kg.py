# -*- coding: utf-8 -*-
import math
from optparse import make_option

from django.core.management.base import BaseCommand

from sadiki.core.models import Requestion, Sadik


class Command(BaseCommand):
    help_text = '''Usage: manage.py calculate_closest_kg'''
    option_list = BaseCommand.option_list + (
        make_option(
            '--only-empty',
            action='store_true',
            dest='only_empty',
            default=False,
            help='Calculate closest kindergarten only for empty requestions'),
    )

    def handle(self, *args, **options):
        print "Calculating closest kindergartens to all requestions in queue"
        if options['only_empty']:
            requestions = Requestion.objects.filter(
                closest_kg=None).select_related('area')
        else:
            requestions = Requestion.objects.all().select_related('area')
        n = 0
        total = requestions.count()
        for requestion in requestions:
            if n % 100 == 0:
                print "Calculating {} requestion from {} total".format(n, total)
                print "Done {:.2f}%".format(n / float(total) * 100)
            if requestion.location:
                find_closest_kg(requestion)
            n += 1
        print "Done!"


def find_closest_kg(requestion):
    kgs = Sadik.objects.filter(
        area__in=requestion.areas.all()).select_related('address')
    closest = None
    for kg in kgs:
        if kg.address.coords:
            distance = measure_distance(requestion.location, kg.address.coords)
            if not closest or closest['distance'] > distance:
                closest = {'kg': kg, 'distance': distance}
    requestion.closest_kg = closest['kg']
    requestion.save()


def measure_distance(coords1, coords2):

    lat1 = coords1[0]
    lon1 = coords1[1]
    lat2 = coords2[0]
    lon2 = coords2[1]

    EARTH_RADIUS = 6378.137
    dLat = (lat2 - lat1) * math.pi / 180
    dLon = (lon2 - lon1) * math.pi / 180
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = EARTH_RADIUS * c
    return d * 1000  # meters
