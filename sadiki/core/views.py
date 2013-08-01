# -*- coding: utf-8 -*-
import json
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from sadiki.conf_settings import DEFAULT_IMPORT_DOCUMENT_NAME
from sadiki.core.models import Sadik, Preference, PREFERENCE_IMPORT_FINISHED, Area, Benefit, AGENT_TYPE_CHOICES, EvidienceDocumentTemplate, REQUESTION_IDENTITY, AgeGroup
from sadiki.anonym.views import Queue as AnonymQueue, RequestionSearch as AnonymRequestionSearch, \
    Registration as AnonymRegistration
from sadiki.operator.views.requestion import Queue as OperatorQueue, Registration as OperatorRegistration,\
    RequestionSearch as OperatorRequestionSearch
from sadiki.supervisor.views import RequestionSearch as SupervisorRequestionSearch


class Frontpage(TemplateView):

    template_name = 'frontpage.html'

    def get(self, request, *args, **kwargs):
        u = request.user
        result = 'anonym_frontpage'
        if u.is_anonymous() or u.is_requester():
            if not Preference.objects.filter(key=PREFERENCE_IMPORT_FINISHED).exists():
                return self.render_to_response({})
        if not u.is_anonymous():
            if u.is_supervisor():
                result = 'supervisor_frontpage'
            elif u.is_operator():
                result = 'operator_frontpage'
            elif u.is_requester():
                result = 'account_frontpage'
            elif u.is_administrator():
                result = 'sadiki_admin:index'
        return HttpResponseRedirect(reverse(result))


class Settings(TemplateView):
    u"""
    Отображение текущих настроек системы
    """

    template_name = 'core/settings.html'

    def get_context_data(self, **kwargs):
        return {'settings': settings}


@csrf_exempt
def sadiki_json(request):
    data = []
    for sadik in Sadik.objects.all():
        if sadik.address.coords:
            data.append({
                'location': sadik.address.coords.tuple,
                'address': sadik.address.text,
                'phone': sadik.phone,
                'name': sadik.short_name,
                'number': sadik.number,
                'url': reverse('sadik_info', args=[sadik.id, ])
            })
    return HttpResponse(simplejson.dumps(data), mimetype='text/json')


class VkontakteFrame(TemplateView):
    u"""
    Отображение текущих настроек системы
    """

    template_name = 'vkontakte.html'

    def get_context_data(self, **kwargs):
        return {'settings': settings}

    def get(self, request):
        return super(VkontakteFrame, self).get(request)


def registration(request, *args, **kwargs):
    if request.user.is_authenticated() and request.user.is_operator():
        return OperatorRegistration.as_view()(request, *args, **kwargs)
    else:
        return AnonymRegistration.as_view()(request, *args, **kwargs)


def queue(request, *args, **kwargs):
    if request.user.is_authenticated() and request.user.is_operator():
        return OperatorQueue.as_view()(request, *args, **kwargs)
    else:
        return AnonymQueue.as_view()(request, *args, **kwargs)


def search(request, *args, **kwargs):
    if request.user.is_authenticated():
        if request.user.is_operator():
            return OperatorRequestionSearch.as_view()(request, *args, **kwargs)
        elif request.user.is_supervisor():
            return SupervisorRequestionSearch.as_view()(request, *args, **kwargs)
    return AnonymRequestionSearch.as_view()(request, *args, **kwargs)


def import_params(request):
    data = {}
    data['SADIKS'] = list(Sadik.objects.filter(active_registration=True).values_list('identifier', flat=True))
    data['AREAS'] = list(Area.objects.all().values_list('name', flat=True))
    data['BENEFITS'] = list(Benefit.objects.all().values_list('name', flat=True))
    data['AGENT_TYPE_CHOICES'] = AGENT_TYPE_CHOICES
    data['MAX_CHILD_AGE'] = settings.MAX_CHILD_AGE
    data['DOCUMENTS_TEMPLATES'] = list(EvidienceDocumentTemplate.objects.filter(
        import_involved=True).values('name', 'regex'))
    data['AGE_GROUPS'] = list(AgeGroup.objects.all().values_list('name', flat=True))
    data["REGION_NAME"] = settings.REGION_NAME
    return HttpResponse(json.dumps(data), mimetype='text/json')