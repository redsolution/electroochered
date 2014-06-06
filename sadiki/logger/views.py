# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from django.conf import settings
from sadiki.account.utils import get_plugin_menu_items, get_plugin_logs
from sadiki.account.views import AccountPermissionMixin
from sadiki.core.models import Requestion, Profile
from sadiki.core.workflow import IMMEDIATELY_PERMANENT_DECISION, \
    PERMANENT_DECISION, DECISION, \
    TEMP_PASS_TRANSFER, TEMP_DISTRIBUTION_TRANSFER, IMMEDIATELY_DECISION, \
    DECISION_DISTRIBUTION, PASS_DISTRIBUTED, \
    DISTRIBUTED_ARCHIVE, STATUS_CHANGE_TRANSITIONS
from sadiki.logger.models import Logger, LoggerMessage
from sadiki.operator.plugins import get_operator_plugin_menu_items, get_operator_plugin_logs
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

    def get(self, request):
        profile = request.user.get_profile()
        data = {'requestions_with_logs': self.get_logs_for_profile(profile),
                'plugin_menu_items': get_plugin_menu_items(),
                'plugin_logs': get_plugin_logs(profile)}
        return self.render_to_response(data)


class OperatorLogs(OperatorPermissionMixin, AccountLogs):
    template_name = 'logger/operator_logs.html'

    def get(self, request, profile_id):
        profile = get_object_or_404(Profile, id=profile_id)
        data = {'requestions_with_logs': self.get_logs_for_profile(profile),
                'profile': profile,
                'plugin_menu_items': get_operator_plugin_menu_items(profile.id),
                'plugin_logs': get_operator_plugin_logs(profile)}
        return self.render_to_response(data)


class LogsByPerson(TemplateView):
    template_name = 'logger/logs_by_person.html'

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        logs = Logger.objects.filter(user=user).order_by('-datetime')
        page_size = 50
        paginator = Paginator(logs, page_size)
        page = request.GET.get('page', 1)
        try:
            paginated_logs = paginator.page(page)
        except PageNotAnInteger:
            paginated_logs = paginator.page(1)
        except EmptyPage:
            paginated_logs = paginator.page(paginator.num_pages)

        log_data = []
        for log in paginated_logs:
            requestion = None
            if log.content_type == ContentType.objects.get_for_model(Requestion):
                requestion = Requestion.objects.get(pk=log.object_id)
            log_data.append((log, LoggerMessage.objects.filter(logger=log),
                             requestion))
        data = {
            'person': user,
            'logs': paginated_logs,
            'log_data': log_data,
            'paginator': paginator,
            'offset': (int(page) - 1) * page_size,
            'page_obj': paginator.page(page),
        }
        return self.render_to_response(data)


class AdmPersonsList(TemplateView):
    template_name = 'anonym/adm_persons_list.html'

    def get(self, request):
        op_perms = Permission.objects.get(codename='is_operator')
        adm_persons = User.objects.filter(groups__permissions=op_perms)
        data = {
            'adm_persons': adm_persons}
        return self.render_to_response(data)

