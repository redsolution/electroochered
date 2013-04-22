# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView, View
from sadiki.core.models import Sadik, Preference, \
    PREFERENCE_MUNICIPALITY_NAME, PREFERENCE_LOCAL_AUTHORITY, \
    PREFERENCE_AUTHORITY_HEAD, PREFERENCE_MUNICIPALITY_NAME_GENITIVE, PREFERENCE_IMPORT_FINISHED
from wkhtmltopdf.views import PDFTemplateResponse
import datetime


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


class GenerateBlankBase(TemplateView):
    templates_by_type = {}

    def get(self, request, requestion):
        blank_type = request.GET.get('type')
        if blank_type not in self.templates_by_type:
            raise AttributeError(u'Неверный тип бланка')
        template_name = self.templates_by_type[blank_type]
#        заполняем context
        local_authority = Preference.objects.get_or_none(key=PREFERENCE_LOCAL_AUTHORITY)
        authority_head = Preference.objects.get_or_none(key=PREFERENCE_AUTHORITY_HEAD)
        municipality_name = Preference.objects.get_or_none(
            key=PREFERENCE_MUNICIPALITY_NAME)
        municipality_name_genitive = Preference.objects.get_or_none(
            key=PREFERENCE_MUNICIPALITY_NAME_GENITIVE)
        context = {'requestion': requestion, 'local_authority': local_authority,
            'authority_head': authority_head, 'media_root': settings.MEDIA_ROOT,
            'municipality_name': municipality_name,
            'municipality_name_genitive': municipality_name_genitive,
            'current_datetime': datetime.datetime.now()}
#        генерируем pdf
        response = PDFTemplateResponse(request=request, template=template_name,
            context=context)
        return response


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
