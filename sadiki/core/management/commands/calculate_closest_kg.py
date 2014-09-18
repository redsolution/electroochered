# -*- coding: utf-8 -*-
import math

from django.core.management.base import BaseCommand

from sadiki.core.models import Requestion, Area, Sadik, Distribution, \
    STATUS_DECISION


class Command(BaseCommand):
    help_text = '''Usage: manage.py send_statistic'''

    def handle(self, *args, **options):
        print "Calculating closest kindergartens to all requestions in queue"
        requestions = Requestion.objects.all()
        for requestion in requestions:
            find_closest_kg(requestion)


def find_closest_kg(requestion):
    kgs = Sadik.objects.filter(area__in=requestion.areas.all())
    closest = None
    for kg in kgs:
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

    EARH_RADIUS = 6378.137
    dLat = (lat2 - lat1) * math.pi / 180
    dLon = (lon2 - lon1) * math.pi / 180
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = EARH_RADIUS * c
    return d * 1000  # meters
