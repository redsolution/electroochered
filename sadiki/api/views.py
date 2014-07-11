# -*- coding: utf-8 -*-
import json
import calendar

from django.utils import simplejson
from django.core import serializers
from django.http import HttpResponse

from sadiki.core.models import Distribution


def get_distributions(request):
    data = Distribution.objects.all().values_list('id', flat=True)
    return HttpResponse(simplejson.dumps(list(data)), mimetype='text/json')


def get_distribution(request, id):
    distribution_qs = Distribution.objects.filter(pk=id)
    if len(distribution_qs) != 1:
        return HttpResponse(simplejson.dumps([0, ]), mimetype='text/json')
    dist = distribution_qs[0]
    data = [{
        'id': dist.id,
        'start': calendar.timegm(dist.init_datetime.timetuple()),
        'end': calendar.timegm(dist.end_datetime.timetuple()),
        'year': dist.year.year,
        'results': [],
    }]
    return HttpResponse(simplejson.dumps(data), mimetype='text/json')
