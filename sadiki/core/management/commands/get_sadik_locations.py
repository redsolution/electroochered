# -*- coding: utf-8 -*-
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from sadiki.core.models import Sadik
from sadiki.core.geocoder import Yandex

class Command(BaseCommand):
    help = "Retrieve locations from sadiks."

    def handle(self, *args, **options):
        for sadik in Sadik.objects.filter(address__coords__isnull=True):
            geocoder = Yandex(bounds=sadik.area.bounds.extent)
            coords = geocoder.geocode(sadik.address.text)
            if coords:
                coords = map(float, coords)
                address = sadik.address
                address.coords = Point(*coords, srid=4326)
                address.save()

