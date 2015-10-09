# -*- coding: utf-8 -*-
import time
import logging
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
        parser.add_argument('-c', '--comment', action='count', default=0)
        parser.add_argument('-q', '--quiet', action='count', default=0)

    def handle(self, *args, **options):
        # configuring logging
        quiet = options['quiet']
        verbose = options['comment']
        log_level = logging.WARN + 10 * quiet - 10 * verbose
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s, %(levelname)s: %(message)s',
            datefmt='%m.%d.%Y %H:%M:%S'
        )

        if not (options['export'] ^ options['import']):
            print 'Error!'
            print 'You must specify exactly one option: --export or --import'
            sys.exit()
        file_name = options.get('file_name') or 'data.djson'
        file_name = os.path.abspath(file_name)
        if options['export']:
            if os.path.exists(file_name):
                user_input = raw_input(
                    'File {} already exists! Overwrite it? (y/n): '.format(
                        file_name)
                )
                while user_input not in ('y', 'n'):
                    user_input = raw_input('Incorrect input!\n')
                if user_input == 'n':
                    print 'Exit...'
                    sys.exit()
            logging.info(u"Начинаю экспорт, запускается dumpdata")
            start_time = time.time()
            management.call_command(
                'dumpdata', '--format', 'djson', '--output', file_name
            )
            logging.info(u"Экспорт завершен, время исполнения: {}:{}".format(
                int(time.time() - start_time) / 60,
                int(time.time() - start_time) % 60,
            ))
            print 'Dump saved successfully to {}'.format(file_name)
        else:
            if not os.path.exists(file_name):
                print 'No such file: {}'.format(file_name)
                print 'Exit...'
                sys.exit(1)
            management.call_command('flush')
            management.call_command('loaddata', file_name)
            print 'Dump from {} restored successfully'.format(file_name)
