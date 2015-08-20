# -*- coding: utf-8 -*-
import json
from itertools import repeat
from multiprocessing import Pool

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.template import loader
from django.template.context import RequestContext
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from rest_framework.renderers import UnicodeJSONRenderer

from pysnippets import gpgtools, dttools
from sadiki.core.models import Distribution, Requestion, Sadik, \
    EvidienceDocument, EvidienceDocumentTemplate, REQUESTION_IDENTITY, \
    STATUS_DECISION, STATUS_DISTRIBUTED, STATUS_DISTRIBUTED_FROM_ES, \
    STATUS_KG_LEAVE, AgeGroup, SadikGroup
from sadiki.api.utils import add_requestions_data
from sadiki.anonym.views import Queue
from sadiki.operator.views.sadik import SadikOperatorPermissionMixin
from sadiki.operator.forms import ConfirmationForm, \
    RequestionIdentityDocumentForm
from sadiki.core.exceptions import RequestionHidden
from sadiki.core.workflow import workflow, DISTRIBUTION_BY_RESOLUTION, \
    REQUESTER_DECISION_BY_RESOLUTION, INNER_TRANSITIONS, \
    SHORT_STAY_DECISION_BY_RESOLUTION, CHANGE_SADIK_GROUP_PLACES
from sadiki.core.signals import post_status_change, pre_status_change
from sadiki.core.serializers import RequestionGeoSerializer, \
    AnonymRequestionGeoSerializer, SadikSerializer, AgeGroupSerializer, \
    SadikGroupSerializer
from sadiki.core.utils import get_current_distribution_year
from sadiki.logger.models import Logger


STATUS_ALREADY_DISTRIBUTED = -1
STATUS_OK = 0
STATUS_DATA_ERROR = 1
STATUS_SYSTEM_ERROR = 2


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = UnicodeJSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


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
        return HttpResponse(content,
                            content_type='application/json; charset=utf-8',
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

        if (requestion.status in
                [STATUS_DISTRIBUTED, STATUS_DISTRIBUTED_FROM_ES] and
                dst_status != STATUS_KG_LEAVE):
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
    return HttpResponse(json.dumps(list(data)), content_type='text/json')


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
        return HttpResponse(json.dumps([0, ]), content_type='text/json')
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
    return HttpResponse(gpgtools.get_signed_json(data),
                        content_type='text/json')


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
        return HttpResponse(json.dumps(response), content_type='text/json')
    raise Http404


@csrf_exempt
def api_sign_test(request):
    status = 'error'
    msgs = []
    if request.method == 'GET':
        msgs.append("Wrong method, use POST instead of GET")
    signed_data = request.POST.get('signed_data')
    if not (signed_data and gpgtools.check_data_sign(
            {'data': request.POST.get('test_string'), 'sign': signed_data})):
        msgs.append("Sing check error")
    test_string = request.POST.get('test_string')
    if not test_string == u"Проверочная строка":
        msgs.append("wrong test_string")
    if not msgs:
        status = 'ok'
        msgs = ["All passed"]
    response = {'sign': gpgtools.sign_data(test_string.encode('utf8')).data,
                'data': msgs, 'status': status}
    return JSONResponse(response)


@csrf_exempt
def api_enc_test(request):
    status = 'error'
    msgs = []
    if request.method == 'GET':
        msgs.append("Wrong method, use POST instead of GET")
    encrypted_data = request.POST.get('encrypted_data')
    if not encrypted_data:
        msgs.append("Encrypted data block is absent")
    else:
        dec_data = gpgtools.decrypt_data(encrypted_data)
        msgs.append(u"Decrypted data: {}".format(
            dec_data.decode('utf8')).encode('utf8'))
        status = 'ok'
    key_name = request.get_host().split('.')[0] + '.electrosadik.ru'
    enc_test_strint = u"Проверка обратного шифрования"
    enc = gpgtools.encrypt_data(enc_test_strint, key_name)
    response = {'data': msgs, 'status': status, 'encrypted_data': enc}
    return JSONResponse(response)


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
    return HttpResponse(json.dumps(response), content_type='text/json')


def get_evidience_documents(request):
    documents = EvidienceDocumentTemplate.objects.filter(
        destination__exact=REQUESTION_IDENTITY
    ).values('id', 'name', 'regex')
    return HttpResponse(json.dumps(list(documents), ensure_ascii=False),
                        content_type='application/json')


@csrf_exempt
def get_requestions(request):
    requestions = RequestionGeoSerializer(
        Requestion.objects.active_queue().filter(location__isnull=False),
        many=True)
    return JSONResponse(requestions.data)


class RequestionsQueue(Queue):
    u"""Возвращает json объект, необходимый для отображения маркеров заявок на
    карте. Если количество заявок больше 2500, используется multiprocessing.Pool
    вычисление идет в 4 процесса.
    """
    paginate_by = None
    fullqueryset = Requestion.objects.all()
    queryset = fullqueryset.hide_distributed()

    def get(self, *args, **kwargs):
        queryset = self.get_queryset()
        # в зависимости от роли пользователя, выбираем, какие данные показывать
        if (self.request.user.is_authenticated() and
                self.request.user.is_operator()):
            serializer = RequestionGeoSerializer
        else:
            serializer = AnonymRequestionGeoSerializer
        try:
            filtered_queryset, form = self.process_filter_form(
                queryset, self.request.GET)
        except (ObjectDoesNotExist, RequestionHidden):
            filtered_queryset = Requestion.objects.none()
        filtered_queryset = filtered_queryset.filter(location__isnull=False)
        requestions_count = len(filtered_queryset)
        if requestions_count < 2500:
            requestions = serializer(filtered_queryset, many=True)
            json_response = requestions.data
        else:
            # распределенно выполняем сериализацию, на 4 процесса
            json_response = []
            processes_number = 4
            pool = Pool(processes=processes_number)
            chunk_size = (requestions_count / processes_number) + 1
            iterable = [filtered_queryset[:chunk_size],
                        filtered_queryset[chunk_size: chunk_size * 2],
                        filtered_queryset[chunk_size * 2: chunk_size * 3],
                        filtered_queryset[chunk_size * 3:]]
            result = pool.imap(
                serialize_requestions, zip(iterable, repeat(serializer)))
            for chunk in result:
                json_response.extend(chunk)
            # вручную завершаем все процессы, иначе они заполняют память
            pool.terminate()
            pool.join()
        return JSONResponse(json_response)


def serialize_requestions((queryset, serializer)):
    requestions = serializer(queryset, many=True)
    return requestions.data


def get_simple_kindergtns(request):
    kgs = Sadik.objects.prefetch_related('age_groups', 'groups').all()
    return JSONResponse(SadikSerializer(kgs, many=True).data)


def get_age_groups(request):
    u"""
    Возвращает просто json-массив со всеми возрастными группами
    """
    age_groups = AgeGroup.objects.all()
    return JSONResponse(AgeGroupSerializer(age_groups, many=True).data)


class GroupsForSadikView(SadikOperatorPermissionMixin, View):

    def get(self, request, sadik_id):
        sgs = SadikGroup.objects.filter(active=True, sadik=sadik_id)
        return JSONResponse(SadikGroupSerializer(sgs, many=True).data)

    def post(self, request, sadik_id):
        data = json.loads(request.body)
        year = get_current_distribution_year()
        kg = get_object_or_404(Sadik, pk=sadik_id)
        for sg_data in data:
            age_group = AgeGroup.objects.get(pk=sg_data['ageGroupId'])
            if sg_data['id']:
                sadik_group = SadikGroup.objects.get(pk=sg_data['id'])
            else:
                try:
                    sadik_group = SadikGroup.objects.get(
                        sadik=kg, active=True, age_group=age_group)
                except ObjectDoesNotExist:
                    sadik_group = SadikGroup(
                        sadik=kg, active=True, age_group=age_group, year=year)
                    sadik_group.set_default_age(age_group)
            places = int(sg_data["capacity"])
            sadik_group.free_places = places
            sadik_group.capacity = places
            sadik_group.save()
            Logger.objects.create_for_action(
                CHANGE_SADIK_GROUP_PLACES,
                context_dict={'sadik_group': sadik_group},
                extra={
                    'user': request.user,
                    'obj': sadik_group,
                    'age_group': sadik_group.age_group
                })
        sgs = SadikGroup.objects.filter(active=True, sadik=sadik_id)
        return JSONResponse(SadikGroupSerializer(sgs, many=True).data)


class PlacesCount(SadikOperatorPermissionMixin, View):
    def get(self, request):
        groups = SadikGroup.objects.filter(active=True)
        total_free_places = groups.aggregate(total_free_places=Sum('free_places'))
        total_capacity = groups.aggregate(total_capacity=Sum('capacity'))
        total_places = total_free_places
        total_places.update(total_capacity)
        return JSONResponse(total_places)
