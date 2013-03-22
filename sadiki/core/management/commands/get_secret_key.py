# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from random import choice


class Command(BaseCommand):
    help_text = '''Usage: manage.py get_secret_key
    generate secret key for django settings
    '''

    def handle(self, *args, **options):
        self.stdout.write(u"%s\n" %
            ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)]))
