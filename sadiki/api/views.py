# -*- coding: utf-8 -*-
import calendar

from django.utils import simplejson
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType

from sadiki.core.models import Distribution, Requestion, Sadik, \
    EvidienceDocument, REQUESTION_IDENTITY


def get_distributions(request):
    data = Distribution.objects.all().values_list('id', flat=True)
    return HttpResponse(simplejson.dumps(list(data)), mimetype='text/json')


def get_distribution(request, id):
    distribution_qs = Distribution.objects.filter(pk=id)
    if len(distribution_qs) != 1:
        return HttpResponse(simplejson.dumps([0, ]), mimetype='text/json')
    dist = distribution_qs[0]
    results = []
    sadiks_ids = Requestion.objects.filter(
        distributed_in_vacancy__distribution=dist).distinct().values_list(
            'distributed_in_vacancy__sadik_group__sadik', flat=True)
    for sadik in Sadik.objects.filter(
            id__in=sadiks_ids).distinct().order_by('number'):
        requestions = Requestion.objects.filter(
            distributed_in_vacancy__distribution=dist,
            distributed_in_vacancy__sadik_group__sadik=sadik).order_by(
                '-birth_date').select_related('profile').select_related(
                    'distributed_in_vacancy__sadik_group__age_group')
        requestions.add_related_documents()
        if requestions:
            kg_dict = {'kindergtn': sadik.id, 'requestions': []}
            for requestion in requestions:
                kg_dict['requestions'].append({
                    'requestion_number': requestion.requestion_number,
                    'name': requestion.name,
                    'birth_date': calendar.timegm(requestion.birth_date.timetuple())})
            results.append(kg_dict)
    data = [{
        'id': dist.id,
        'start': calendar.timegm(dist.init_datetime.timetuple()),
        'end': calendar.timegm(dist.end_datetime.timetuple()),
        'year': dist.year.year,
        'results': results,
    }]
    return HttpResponse(simplejson.dumps(data), mimetype='text/json')


@csrf_exempt
def get_child(request):
    doc = request.POST.get('doc')
    requestion_ct = ContentType.objects.get_for_model(Requestion)
    requestion_ids = EvidienceDocument.objects.filter(
        content_type=requestion_ct,
        document_number=doc,
        template__destination=REQUESTION_IDENTITY).values_list('object_id',
                                                               flat=True)
    print requestion_ids
    print doc
    return HttpResponse()
