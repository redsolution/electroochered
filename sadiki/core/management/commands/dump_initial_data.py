# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Dump initial data"

    def handle(self, *args, **options):
        call_command('dumpdata', 
            'core.BenefitCategory', 'core.EvidienceDocumentTemplate', use_natural_keys=True)
