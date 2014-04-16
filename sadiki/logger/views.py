# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from django.conf import settings
from sadiki.account.utils import get_plugin_menu_items
from sadiki.account.views import AccountPermissionMixin
from sadiki.core.models import Requestion, Profile
from sadiki.core.workflow import IMMEDIATELY_PERMANENT_DECISION, \
    PERMANENT_DECISION, DECISION, \
    TEMP_PASS_TRANSFER, TEMP_DISTRIBUTION_TRANSFER, IMMEDIATELY_DECISION, \
    DECISION_DISTRIBUTION, PASS_DISTRIBUTED, \
    DISTRIBUTED_ARCHIVE, STATUS_CHANGE_TRANSITIONS
from sadiki.logger.models import Logger
from sadiki.operator.plugins import get_operator_plugin_menu_items
from sadiki.operator.views.base import OperatorPermissionMixin

DECISION_TRANSFERS = (DECISION, IMMEDIATELY_DECISION, PERMANENT_DECISION,
                     IMMEDIATELY_PERMANENT_DECISION, TEMP_DISTRIBUTION_TRANSFER,
                     TEMP_PASS_TRANSFER)
TEMP_DECISION_TRANSFERS = (TEMP_DISTRIBUTION_TRANSFER, TEMP_PASS_TRANSFER)
DISTRIBUTION_TRANSFERS = (DECISION_DISTRIBUTION, PASS_DISTRIBUTED,)
DISMISS_TRANSFERS = (DISTRIBUTED_ARCHIVE,)


class RequestionLogs(TemplateView):
    u"""
    Отображение публичных логов изменений заявки
    """
    template_name = "logger/requestion_logs.html"

    def get(self, request, requestion_id):
        requestion = get_object_or_404(Requestion, id=requestion_id)
        logs = Logger.objects.filter(content_type=ContentType.objects.get_for_model(Requestion),
            object_id=requestion.id).order_by('datetime')
        logs_with_messages = []
        for log in logs:
            messages = log.loggermessage_set.filter_for_user(request.user)
            if log.action_flag in STATUS_CHANGE_TRANSITIONS or messages:
                logs_with_messages.append([log, messages])
        if request.user.is_authenticated() and request.user.is_operator():
            return HttpResponseRedirect(reverse("operator_logs", kwargs={'profile_id': requestion.profile.id}))
        return self.render_to_response({'logs_with_messages': logs_with_messages, 'requestion': requestion})


class AccountLogs(AccountPermissionMixin, TemplateView):
    template_name = 'logger/account_logs.html'

    def get_logs_for_profile(self, profile):
        requestions = profile.requestion_set.all()
        requestions_with_logs = []
        for requestion in requestions:
            logs = Logger.objects.filter(content_type=ContentType.objects.get_for_model(Requestion),
            object_id=requestion.id).order_by('datetime')
            logs_with_messages = []
            for log in logs:
                messages = log.loggermessage_set.filter_for_user(self.request.user)
                if log.action_flag in STATUS_CHANGE_TRANSITIONS or messages:
                    logs_with_messages.append([log, messages])
            requestions_with_logs.append([requestion, logs_with_messages])
        return requestions_with_logs

    def get_pdata_logs(self, profile):
        from personal_data.logging import PERSONAL_DATA_ACTION_FLAGS
        logs = Logger.objects.filter(user=profile.user,
                                     action_flag__in=PERSONAL_DATA_ACTION_FLAGS)
        return logs

    def get(self, request):
        profile = request.user.get_profile()
        data = {'requestions_with_logs': self.get_logs_for_profile(profile),
                'plugin_menu_items': get_plugin_menu_items()}
        if 'personal_data' in settings.INSTALLED_APPS:
            pdata_logs = self.get_pdata_logs(profile)
            data.update({'pdata_logs': pdata_logs})
        return self.render_to_response(data)


class OperatorLogs(OperatorPermissionMixin, AccountLogs):
    template_name = 'logger/operator_logs.html'

    def get(self, request, profile_id):
        profile = get_object_or_404(Profile, id=profile_id)
        data = {'requestions_with_logs': self.get_logs_for_profile(profile),
                'profile': profile,
                'plugin_menu_items': get_operator_plugin_menu_items(profile.id)}
        if 'personal_data' in settings.INSTALLED_APPS:
            pdata_logs = self.get_pdata_logs(profile)
            data.update({'pdata_logs': pdata_logs})
        return self.render_to_response(data)



