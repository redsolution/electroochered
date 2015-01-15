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
    STATUS_DECISION, STATUS_DISTRIBUTED, STATUS_DISTRIBUTED_FROM_ES
from sadiki.api.utils import add_requestions_data
from sadiki.operator.forms import ConfirmationForm, \
    RequestionIdentityDocumentForm
from sadiki.core.workflow import workflow, DISTRIBUTION_BY_RESOLUTION, \
    REQUESTER_DECISION_BY_RESOLUTION, INNER_TRANSITIONS, \
    SHORT_STAY_DECISION_BY_RESOLUTION
from sadiki.core.signals import post_status_change, pre_status_change
from sadiki.logger.models import Logger


STATUS_ALREADY_DISTRIBUTED = -1
STATUS_OK = 0
STATUS_DATA_ERROR = 1
STATUS_SYSTEM_ERROR = 2


class SignJSONResponseMixin(object):
    u"""
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
    u"""
    Реализация метода api для изменения статуса заявки через запрос от
    ЭлектроСада
    """
    form = ConfirmationForm

    def post(self, request, *args, **kwargs):
        # Начальные значения
        status_code = STATUS_DATA_ERROR
        err_msg = None
        data = kwargs['data']
        dst_status = int(data['dst_status'])
        requestion = Requestion.objects.get(pk=data['requestion_id'])
        # параноидальная проверка целостности данных
        if requestion.requestion_number != data['requestion_number']:
            err_msg = u"Ошибка проверки данных заявки: номер заявки отличается"\
                      u"от указанного в профиле"
            result = {'status_code': STATUS_DATA_ERROR, 'err_msg': {
                '__all__': err_msg,
            }}
            return self.render_to_response(result)

        if requestion.status in [STATUS_DISTRIBUTED,
                                 STATUS_DISTRIBUTED_FROM_ES]:
            err_msg = u"Заявка зачислена в Электроочереди, действие невозможно"
            if dst_status == STATUS_DISTRIBUTED_FROM_ES:
                err_msg = u"Заявка уже зачислена в Электроочереди"
            result = {'status_code': STATUS_ALREADY_DISTRIBUTED,
                      'err_msg': {'__all__': err_msg}}
            return self.render_to_response(result)

        transition_indexes = workflow.available_transitions(
            src=requestion.status, dst=dst_status)
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
            if transition.index in INNER_TRANSITIONS:
                if Requestion.objects.filter(
                        id=requestion.id, status=transition.src).update(
                        status=transition.dst):
                    Logger.objects.create_for_action(
                        transition.index, context_dict=data,
                        extra={'obj': requestion})
                    status_code = STATUS_OK
                else:
                    status_code = STATUS_DATA_ERROR
                    err_msg = u"Проверьте статус заявки в Электроочереди"
            else:
                form = self.form(requestion=requestion,
                                 data={'reason': data.get('reason'),
                                       'transition': transition.index,
                                       'confirm': "yes"},
                                 initial={'transition': transition.index})
                if form.is_valid():
                    pre_status_change.send(
                        sender=Requestion, request=request,
                        requestion=requestion, transition=transition, form=form)
                    requestion.status = transition.dst
                    requestion.save()
                    post_status_change.send(
                        sender=Requestion, request=request,
                        requestion=requestion, transition=transition, form=form)
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
    u"""
    Получаем список заявок, которые были зачислены по резолюции
    """
    def post(self, request, *args, **kwargs):
        data = kwargs['data']
        last_import_datetime = dttools.datetime_from_stamp(data['last_import'])
        ridx = Logger.objects.filter(
            action_flag__in=[DISTRIBUTION_BY_RESOLUTION,
                             REQUESTER_DECISION_BY_RESOLUTION,
                             SHORT_STAY_DECISION_BY_RESOLUTION, ],
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
            reqs = requestions.filter(
                distributed_in_vacancy__sadik_group__sadik=sadik,
                status__in=[STATUS_DISTRIBUTED, STATUS_DECISION])
            if reqs:
                req_list = add_requestions_data(reqs, request)
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
    data = json.loads(request.body)
    signed_data = data.get('signed_data')
    if not (signed_data and gpgtools.check_data_sign(
            {'data': data.get('id'), 'sign': signed_data})):
        raise Http404
    _id = data.get('id')
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
    options = data.get('options')
    for sadik in Sadik.objects.filter(
            id__in=sadiks_ids).distinct().order_by('number'):
        requestions = Requestion.objects.filter(
            distributed_in_vacancy__distribution=dist,
            distributed_in_vacancy__sadik_group__sadik=sadik,
            status__in=[STATUS_DECISION, STATUS_DISTRIBUTED])
        if options.get('only_decision'):
            requestions = requestions.filter(status=STATUS_DECISION)
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
    data = json.loads(request.body)
    if not data['data']:
        return HttpResponse()
    if gpgtools.check_data_sign(data):
        requestion_ct = ContentType.objects.get_for_model(Requestion)
        requestion_ids = EvidienceDocument.objects.filter(
            content_type=requestion_ct, document_number=data['data'],
            template__destination=REQUESTION_IDENTITY
        ).values_list('object_id', flat=True)
        if not requestion_ids:
            return HttpResponse()
        requestions = Requestion.objects.filter(id__in=requestion_ids)
        data = add_requestions_data(requestions, request)
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
    if not (signed_data and gpgtools.check_data_sign(
            {'data': request.POST.get('test_string'), 'sign': signed_data})):
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
