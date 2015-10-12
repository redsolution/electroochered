from django.http import Http404, HttpResponse
from django.views.generic.base import TemplateView
import os
from django.conf import settings
import ho.pisa as pisa
import datetime
import StringIO
from sadiki.core.models import Preference, \
    PREFERENCE_MUNICIPALITY_NAME, PREFERENCE_LOCAL_AUTHORITY, \
    PREFERENCE_AUTHORITY_HEAD, PREFERENCE_MUNICIPALITY_NAME_GENITIVE
from django.template import Context
from django.template.loader import get_template


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


def generate_pdf(template_name, context_dict):
    context = Context(context_dict)
    template = get_template(template_name)
    html = template.render(context)
    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(
        StringIO.StringIO(html.encode("UTF-8")), dest=result,
        encoding='UTF-8', link_callback=fetch_resources)
    return result


class GenerateBlankBase(TemplateView):
    templates_by_type = {}

    def get(self, request, requestion):
        blank_type = request.GET.get('type')
        if blank_type not in self.templates_by_type:
            raise Http404
        template_name = self.templates_by_type[blank_type]

        local_authority = Preference.objects.get_or_none(key=PREFERENCE_LOCAL_AUTHORITY)
        authority_head = Preference.objects.get_or_none(key=PREFERENCE_AUTHORITY_HEAD)
        municipality_name = Preference.objects.get_or_none(
            key=PREFERENCE_MUNICIPALITY_NAME)
        municipality_name_genitive = Preference.objects.get_or_none(
            key=PREFERENCE_MUNICIPALITY_NAME_GENITIVE)
        context_dict = {'requestion': requestion, 'local_authority': local_authority,
            'authority_head': authority_head, 'media_root': settings.MEDIA_ROOT,
            'municipality_name': municipality_name,
            'municipality_name_genitive': municipality_name_genitive,
            'current_datetime': datetime.datetime.now()}
        result = generate_pdf(template_name, context_dict)
        response = HttpResponse(result.getvalue(),
                                content_type='application/pdf')
        return response
