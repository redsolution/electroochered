# -*- coding: utf-8 -*-
from django.core import management, serializers
from django.apps import apps


class Command(management.base.BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('model_name')
        parser.add_argument('--format', action='store', default='djson',
                            dest='format')
        parser.add_argument('--start', action='store', default=0, dest='start')
        parser.add_argument('--end', action='store', default=-1, dest='end')
        parser.add_argument('--output', action='store', default='data.djson',
                            dest='file_name')

    def handle(self, *args, **options):
        ser_format = options['format']
        model_name = options['model_name']
        start = options['start']
        end = options['end']
        fname = options['file_name']

        model = apps.get_model(model_name)
        queryset = model.objects.order_by('pk')[start:end]
        stream = open(fname, 'w')
        serializers.serialize(ser_format, queryset, stream=stream)
        stream.close()
