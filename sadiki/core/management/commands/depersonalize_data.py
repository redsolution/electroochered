# -*- coding: utf-8 -*-
import os
import sys
from django.core import management


class Command(management.base.BaseCommand):
    # help = "Dumps or loads depersonalized json data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--export',
            action='store_true',
            dest='export',
            default=False,
        )
        parser.add_argument(
            '--import',
            action='store_true',
            dest='import',
            default=False,
        )
        parser.add_argument('file_name', nargs='?')

    def handle(self, *args, **options):
        if not (options['export'] ^ options['import']):
            print 'You must specify exactly one option: --export or --import'
            return
        file_name = options.get('file_name') or 'data.djson'
        file_name = os.path.abspath(file_name)
        if options['export']:
            if os.path.exists(file_name):
                user_input = raw_input(
                    'File {} already exists! Overwrite it? (y/n)\n'.format(
                        file_name)
                )
                while user_input not in ('y', 'n'):
                    user_input = raw_input('Incorrect input!\n')
                if user_input == 'n':
                    print 'Exit...'
                    return
            management.call_command(
                'dumpdata', '--format', 'djson', '--output', file_name
            )
            print 'Dump saved successfully to {}'.format(file_name)
        else:
            if not os.path.exists(file_name):
                print 'No such file: {}'.format(file_name)
                print 'Exit...'
                sys.exit(1)
            management.call_command('flush')
            management.call_command('loaddata', file_name)
            print 'Dump from {} restored successfully'.format(file_name)
