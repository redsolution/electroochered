from django.views.generic.base import TemplateView
from sadiki.core.permissions import RequirePermissionsMixin

class SadikiMap(RequirePermissionsMixin, TemplateView):
    template_name = 'openbox_map.html'
