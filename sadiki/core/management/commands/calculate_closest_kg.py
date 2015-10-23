# -*- coding: utf-8 -*-
from optparse import make_option

from django.core.management.base import BaseCommand

from sadiki.core.models import Requestion
from sadiki.core.utils import find_closest_kg


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
                closest_kg=None).prefetch_related('areas')
        else:
            requestions = Requestion.objects.all().prefetch_related('areas')
        n = 0
        total = requestions.count()
        for requestion in requestions:
            if n % 100 == 0:
                print "Calculating {} requestion from {} total".format(n, total)
                print "Done {:.2f}%".format(n / float(total) * 100)
            if requestion.location:
                find_closest_kg(requestion, verbose=True)
            n += 1
        print "Done!"

