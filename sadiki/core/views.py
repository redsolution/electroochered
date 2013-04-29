# -*- coding: utf-8 -*-
import os
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import Context
from django.template.loader import get_template
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView, View
from sadiki.core.models import Sadik, Preference, \
    PREFERENCE_MUNICIPALITY_NAME, PREFERENCE_LOCAL_AUTHORITY, \
    PREFERENCE_AUTHORITY_HEAD, PREFERENCE_MUNICIPALITY_NAME_GENITIVE, PREFERENCE_IMPORT_FINISHED
import ho.pisa as pisa
import datetime
import StringIO


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


def fetch_resources(uri, rel):
    """
    Callback to allow xhtml2pdf/reportlab to retrieve Images,Stylesheets, etc.
    `uri` is the href attribute from the html link element.
    `rel` gives a relative path, but it's not used here.

    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT,
                            uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT,
                            uri.replace(settings.STATIC_URL, ""))
    else:
        path = os.path.join(settings.STATIC_ROOT,
                            uri.replace(settings.STATIC_URL, ""))

        if not os.path.isfile(path):
            path = os.path.join(settings.MEDIA_ROOT,
                                uri.replace(settings.MEDIA_URL, ""))

    return path


class GenerateBlankBase(TemplateView):
    templates_by_type = {}

    def get(self, request, requestion):
        blank_type = request.GET.get('type')
        if blank_type not in self.templates_by_type:
            raise Http404
        template_name = self.templates_by_type[blank_type]
        template = get_template(template_name)
        local_authority = Preference.objects.get_or_none(key=PREFERENCE_LOCAL_AUTHORITY)
        authority_head = Preference.objects.get_or_none(key=PREFERENCE_AUTHORITY_HEAD)
        municipality_name = Preference.objects.get_or_none(
            key=PREFERENCE_MUNICIPALITY_NAME)
        municipality_name_genitive = Preference.objects.get_or_none(
            key=PREFERENCE_MUNICIPALITY_NAME_GENITIVE)
        context = Context({'requestion': requestion, 'local_authority': local_authority,
            'authority_head': authority_head, 'media_root': settings.MEDIA_ROOT,
            'municipality_name': municipality_name,
            'municipality_name_genitive': municipality_name_genitive,
            'current_datetime': datetime.datetime.now()})
        html = template.render(context)
        result = StringIO.StringIO()

        pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")),
                                                dest=result,
                                                encoding='UTF-8',
                                                link_callback=fetch_resources)
        if not pdf.err:
            response = HttpResponse(result.getvalue(),
                                                        mimetype='application/pdf')
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
