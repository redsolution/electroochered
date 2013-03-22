# -*- coding: utf-8 -*-
from django.utils import simplejson
from django.utils.safestring import mark_safe
from sadiki.core.models import EvidienceDocumentTemplate
import re
import sys
import os
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO



class NoCacheMiddleware(object):
    def process_response(self, request, response):
        response['Pragma'] = 'no-cache'
        response['Cache-Control'] = 'no-cache must-revalidate proxy-revalidate'
        return response

HEAD_TAG_RE = re.compile(r'(</\s*head\s*>)', re.IGNORECASE)
DOCUMENT_TEMPLATE_SCRIPT = '''
<script type="text/javascript">
var DOCUMENT_TEMPLATES = %s;
</script>
'''

class SettingsJSMiddleware(object):

    def process_response(self, request, response):
        """Add some script to the end of head element"""
        documents_template = simplejson.dumps(
            dict([(template.id, {
                    'name': template.name,
                    'regexp': template.regex,
                    'help_text': template.format_tips,
                    'id': template.id,
                    'benefits': list(template.benefit_set.values_list('id', flat=True))
                })
                for template in EvidienceDocumentTemplate.objects.all()]))
        try:
            def add_url_definition(match):
                return mark_safe(DOCUMENT_TEMPLATE_SCRIPT % documents_template + match.group())
            if 'text/html' in response['Content-Type']:
                response.content = HEAD_TAG_RE.sub(add_url_definition, response.content)
                return response
        except:
            return response
        else:
            return response

class LogPIDMiddleware(object):

    def process_request(self, request):
        request.META['wsgi.errors'].write(
            'PID: %s THREAD: %s PATH: %s\n' % (
                os.getpid(), sys._current_frames().items()[0][0], request.META['PATH_INFO'])
        )
