# -*- coding: utf-8 -*-
import json

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.template import loader
from django.template.context import RequestContext
from django.utils import simplejson
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from pysnippets import gpgtools, dttools
from sadiki.core.models import Distribution, Requestion, Sadik, \
    EvidienceDocument, EvidienceDocumentTemplate, REQUESTION_IDENTITY, \
    STATUS_DECISION, STATUS_DISTRIBUTED
from sadiki.api.utils import sign_is_valid, add_requestions_data
from sadiki.operator.forms import ConfirmationForm, \
    RequestionIdentityDocumentForm
from sadiki.core.workflow import workflow, DISTRIBUTION_BY_RESOLUTION, \
    REQUESTER_DECISION_BY_RESOLUTION
from sadiki.core.signals import post_status_change, pre_status_change
from sadiki.logger.models import Logger


STATUS_ALREADY_DISTRIBUTED = -1
STATUS_OK = 0
STATUS_DATA_ERROR = 1
STATUS_SYSTEM_ERROR = 2


class SignJSONResponseMixin(object):
    """
    Миксин, который выполняет проверку корректности подписи данных входящего
    запроса и формирует json в ответ
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        # если данные не проходят gpg проверку, возвращаем 403
        data = json.loads(request.body)
        if not gpgtools.check_data_sign(data):
            return HttpResponseForbidden(loader.render_to_string(
                '403.html', context_instance=RequestContext(request)))
        kwargs.update({'data': data['data']})
        return super(SignJSONResponseMixin, self).dispatch(
            request, *args, **kwargs)

    def render_to_response(self, context):
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **kwargs):
        return HttpResponse(content, mimetype='application/json; charset=utf-8',
                            **kwargs)

    def convert_context_to_json(self, context):
        return gpgtools.get_signed_json(context)


class ChangeRequestionStatus(SignJSONResponseMixin, View):
    """
    Реализация метода api для изменения статуса заявки через запрос от
    ЭлектроСада
    """
    form = ConfirmationForm

    def post(self, request, *args, **kwargs):
        # Начальные значения
        status_code = STATUS_DATA_ERROR
        err_msg = None
        data = kwargs['data']
        requestion = Requestion.objects.get(pk=data['requestion_id'])
        # параноидальная проверка целостности данных
        if requestion.requestion_number != data['requestion_number']:
            err_msg = u"Ошибка проверки данных заявки: номер заявки отличается"\
                      u"от указанного в профиле"
            result = {'status_code': STATUS_DATA_ERROR, 'err_msg': {
                '__all__': err_msg,
            }}
            return self.render_to_response(result)

        if requestion.status == STATUS_DISTRIBUTED:
            err_msg = u"Заявка зачислена в Электроочереди, действие невозможно"
            result = {'status_code': STATUS_ALREADY_DISTRIBUTED,
                      'err_msg': {'__all__': err_msg}}
            return self.render_to_response(result)

        transition_indexes = workflow.available_transitions(
            src=requestion.status, dst=int(data['dst_status']))
        # TODO: Проверка на корректность ДОУ?
        # sadik = requestion.distributed_in_vacancy.sadik_group.sadik
        # Если в форме передается свидетельство о рождении и текущий
        # документ у заявки - временный, меняем
        if 'document_number' in data and requestion.evidience_documents()[0].fake:
            form_data = {
                'template': data['template'],
                'document_number': data['document_number'],
            }
            form = RequestionIdentityDocumentForm(
                instance=requestion, data=form_data)
            if form.is_valid():
                form.save()
                requestion.evidience_documents().filter(fake=True).delete()
            else:
                err_msg = {}
                for error in form.errors:
                    err_msg[error] = form.errors[error]
                result = {'status_code': status_code, 'err_msg': err_msg}
                return self.render_to_response(result)
        if transition_indexes:
            transition = workflow.get_transition_by_index(transition_indexes[0])
            form = self.form(requestion=requestion,
                             data={'reason': data['reason'],
                                   'transition': transition.index,
                                   'confirm': "yes"},
                             initial={'transition': transition.index})
            if form.is_valid():
                pre_status_change.send(
                    sender=Requestion, request=request, requestion=requestion,
                    transition=transition, form=form)
                requestion.status = transition.dst
                requestion.save()
                post_status_change.send(
                    sender=Requestion, request=request, requestion=requestion,
                    transition=transition, form=form)
                status_code = STATUS_OK
            else:
                err_msg = {}
                for error in form.errors:
                    err_msg[error] = form.errors[error]
        else:
            err_msg = {
                '__all__': u"Невозможно изменить статус заявки в электроочереди"
            }
        result = {'status_code': status_code, 'err_msg': err_msg}
        return self.render_to_response(result)


class GetRequestionsByResolution(SignJSONResponseMixin, View):
    """
    Получаем список заявок, которые были зачислены по резолюции
    """
    def post(self, request, *args, **kwargs):
        data = kwargs['data']
        last_import_datetime = dttools.datetime_from_stamp(data['last_import'])
        ridx = Logger.objects.filter(
            action_flag__in=[DISTRIBUTION_BY_RESOLUTION,
                             REQUESTER_DECISION_BY_RESOLUTION],
            datetime__gte=last_import_datetime
        ).values_list('object_id', flat=True)
        # если зачислений по резолюции за указанные период не было
        if not ridx:
            return self.render_to_response({'status_code': STATUS_OK,
                                            'data': []})
        requestions = Requestion.objects.filter(id__in=ridx)
        sadiks_ids = requestions.distinct().values_list(
            'distributed_in_vacancy__sadik_group__sadik', flat=True)
        results = []
        for sadik in Sadik.objects.filter(
                id__in=sadiks_ids).distinct().order_by('number'):
            requestions = requestions.filter(
                distributed_in_vacancy__sadik_group__sadik=sadik,
                status__in=[STATUS_DISTRIBUTED, STATUS_DECISION])
            if requestions:
                req_list = add_requestions_data(requestions, request)
                kg_dict = {'kindergtn': sadik.id, 'requestions': req_list}
                results.append(kg_dict)
        return self.render_to_response({
            'status_code': STATUS_OK, 'data': results})


def get_distributions(request):
    data = Distribution.objects.all().values_list('id', flat=True)
    return HttpResponse(simplejson.dumps(list(data)), mimetype='text/json')


@csrf_exempt
def get_distribution(request):
    if request.method == 'GET':
        raise Http404
    signed_data = request.POST.get('signed_data')
    if not (signed_data and sign_is_valid(signed_data)):
        raise Http404
    _id = request.POST.get('id')
    if not _id:
        raise Http404
    distribution_qs = Distribution.objects.filter(pk=_id)
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
            distributed_in_vacancy__sadik_group__sadik=sadik,
            status__in=[STATUS_DECISION, STATUS_DISTRIBUTED]).order_by(
                '-birth_date').select_related('profile').select_related(
                    'distributed_in_vacancy__sadik_group__age_group')
        if requestions:
            req_list = add_requestions_data(requestions, request)
            kg_dict = {'kindergtn': sadik.id, 'requestions': req_list}
            results.append(kg_dict)

    data = [{
        'id': dist.id,
        'start': dttools.date_to_stamp(dist.init_datetime),
        'end': dttools.date_to_stamp(dist.end_datetime),
        'year': dist.year.year,
        'results': results,
    }]
    return HttpResponse(gpgtools.get_signed_json(data), mimetype='text/json')


@csrf_exempt
def get_child(request):
    if request.method == 'GET':
        raise Http404
    doc = request.POST.get('doc')
    signed_data = request.POST.get('sign')
    if sign_is_valid(signed_data):
        requestion_ct = ContentType.objects.get_for_model(Requestion)
        requestion_ids = EvidienceDocument.objects.filter(
            content_type=requestion_ct, document_number=doc,
            template__destination=REQUESTION_IDENTITY).values_list('object_id',
                                                                   flat=True)
        if not requestion_ids:
            return HttpResponse()
        requestions = Requestion.objects.filter(id__in=requestion_ids)
        data = []
        for requestion in requestions:
            url = request.build_absolute_uri(reverse('requestion_logs',
                                                     args=(requestion.id, )))
            req_dict = {
                'requestion_number': requestion.requestion_number,
                'status': requestion.status,
                'id': requestion.id,
                'url': url,
            }
            if requestion.distribution_datetime:
                req_dict['distribution_datetime'] = dttools.date_to_stamp(
                    requestion.distribution_datetime)
            data.append(req_dict)
        response = [{'sign': gpgtools.sign_data(data).data, 'data': data}]
        return HttpResponse(simplejson.dumps(response), mimetype='text/json')
    raise Http404


@csrf_exempt
def api_test(request):
    status = 'error'
    msg = None
    if request.method == 'GET':
        msg = "Wrong method, use POST instead of GET"
    signed_data = request.POST.get('signed_data')
    if not (signed_data and sign_is_valid(signed_data)):
        msg = "Sing check error"
    test_string = request.POST.get('test_string')
    if not test_string == u"Проверочная строка":
        msg = "wrong test_string"
    if not msg:
        status = 'ok'
        msg = "All passed"
    response = [{'sign': gpgtools.sign_data(msg).data,
                 'data': msg, 'status': status}]
    return HttpResponse(simplejson.dumps(response), mimetype='text/json')


@csrf_exempt
def get_kindergartens(request):
    data = []
    for sadik in Sadik.objects.all():
        data.append({
            'id': sadik.id,
            'address': sadik.address.text,
            'phone': sadik.phone,
            'name': sadik.short_name,
            'head_name': sadik.head_name,
            'email': sadik.email,
            'site': sadik.site,
        })
    response = [{'sign': gpgtools.sign_data(data).data, 'data': data}]
    return HttpResponse(simplejson.dumps(response), mimetype='text/json')


def get_evidience_documents(request):
    documents = EvidienceDocumentTemplate.objects.filter(
        destination__exact=REQUESTION_IDENTITY
    ).values('id', 'name', 'regex')
    return HttpResponse(simplejson.dumps(list(documents), ensure_ascii=False),
                        mimetype='application/json')
