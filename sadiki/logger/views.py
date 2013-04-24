# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from sadiki.account.views import AccountPermissionMixin
from sadiki.core.models import Requestion, Sadik, Area, STATUS_CHOICES, \
    Distribution
from sadiki.core.utils import get_current_distribution_year
from sadiki.core.workflow import CHANGE_PREFERRED_SADIKS, \
    CHANGE_PREFERRED_SADIKS_BY_OPERATOR, ADD_REQUESTION, REQUESTION_REGISTRATION, \
    REQUESTION_IMPORT, IMMEDIATELY_PERMANENT_DECISION, \
    PERMANENT_DECISION, DECISION, \
    TEMP_PASS_TRANSFER, TEMP_DISTRIBUTION_TRANSFER, IMMEDIATELY_DECISION, \
    PASS_GRANTED, DECISION_DISTRIBUTION, \
    PASS_DISTRIBUTED, \
    workflow, DISTRIBUTED_ARCHIVE, DECISION_ABSENT, \
    DECISION_NOT_APPEAR, \
    ABSENT_REMOVE_REGISTRATION, NOT_APPEAR_REMOVE_REGISTRATION
from sadiki.logger.forms import ReportAgeGroupForm, ReportDateForm
from sadiki.logger.models import Logger, Report, \
    REPORT_FILLABILITY, REPORTS_CHOICES, REPORT_TRANSITIONS, REPORT_STATUSES, \
    REPORT_SADIKS_REQUESTS
from sadiki.operator.views.base import OperatorPermissionMixin
import datetime

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
        return self.render_to_response({'logs': logs, 'requestion': requestion})


class RequestionLogsForAccount(AccountPermissionMixin, RequestionLogs):
    u"""
    Отображение логов изменений заявки для заявителя
    """
    template_name = "logger/requestion_logs_for_account.html"


class RequestionLogsForOperator(OperatorPermissionMixin, RequestionLogs):
    u"""
    Отображение логов изменений заявки для оператора
    """
    template_name = "logger/requestion_logs_for_operator.html"


class Reports(OperatorPermissionMixin, TemplateView):
    template_name = 'logger/reports.html'

    def get(self, request):
        return self.render_to_response({"report_types": dict(REPORTS_CHOICES)})

one_day = datetime.timedelta(days=1)


def get_fillability_report_data(age_group, from_date, to_date):
    logs = Logger.objects.filter(
                Q(datetime__gt=from_date - one_day) &
                Q(datetime__lt=to_date + one_day), age_groups=age_group)
    areas_info = []
    for area in Area.objects.all():
        sadiks_info = []
        for sadik in area.sadik_set.all():
#            вычисляем показатели на начало отчетного периода
            logs_for_begin = Logger.objects.filter(
                vacancy__sadik_group__sadik=sadik, datetime__lte=from_date)
            distributed_fo_begin = logs_for_begin.filter(
                action_flag__in=DISTRIBUTION_TRANSFERS,).count()
            dismiss_begin = logs_for_begin.filter(
                action_flag__in=DISMISS_TRANSFERS).count()
#            сколько детей числилось в ДОУ
            requestions_for_sadik_begin = distributed_fo_begin - dismiss_begin
            sadik_logs = logs.filter(vacancy__sadik_group__sadik=sadik)
#            скольким было направлено
            decision_number = sadik_logs.filter(
                action_flag__in=DECISION_TRANSFERS,
                vacancy__sadik_group__sadik=sadik).count()
#            сколько было зачислено
            distribution_number = sadik_logs.filter(
                action_flag__in=DISTRIBUTION_TRANSFERS).count()
#            сколько было отчислено
            dismiss_number = sadik_logs.filter(
                action_flag__in=DISMISS_TRANSFERS).count()
            requestions_for_sadik_end = requestions_for_sadik_begin + \
                distribution_number - dismiss_number
            sadiks_info.append({'sadik_name': unicode(sadik),
                                'requestions_for_sadik_begin': requestions_for_sadik_begin,
                                'decision_number': decision_number,
                                'distribution_number': distribution_number,
                                'dismiss_number': dismiss_number,
                                'requestions_for_sadik_end': requestions_for_sadik_end, })
        areas_info.append(
            {'area_name': unicode(area), 'sadiks_info': sadiks_info})

    return {'areas_info': areas_info}


def get_transitions_report_data(from_date, to_date):
    logs = Logger.objects.filter(
                Q(datetime__gt=from_date - one_day) &
                Q(datetime__lt=to_date + one_day))
    transitions_info = []
    for transition in workflow.transitions:
        number = logs.filter(action_flag=transition.index).count()
        transitions_info.append(
            {'transition_comment': unicode(transition.comment), 'number': number})
    return {"transitions_info": transitions_info}


def get_statuses_report_data(from_date, to_date):
    logs = Logger.objects.filter(
                Q(datetime__gt=from_date - one_day) &
                Q(datetime__lt=to_date + one_day))
    statuses_info = []
    for status in STATUS_CHOICES:
        transitions = workflow.available_transitions(dst=status[0])
        areas_info = []
        for area in Area.objects.all():
            to_status_number = logs.filter(action_flag__in=transitions).count()
            areas_info.append({'to_status_number': to_status_number})
        statuses_info.append(
            {'status': dict(STATUS_CHOICES)[status[0]], 'areas_info': areas_info})

    return {'statuses_info': statuses_info, 'areas': [unicode(area)
        for area in Area.objects.all()]}


def get_sadiks_requests_report_data(from_date, to_date, age_group):
    one_day = datetime.timedelta(days=1)
    logs = Logger.objects.filter(Q(datetime__lt=to_date + one_day,
        datetime__gt=from_date - one_day), age_groups=age_group)
    areas_info = []
    for area in Area.objects.all():
        sadiks_info = []
        for sadik in Sadik.objects.filter(area=area):
#                при регистрации кол-во указаний в кач-ве приоритетного
            registration_set_pref_number = logs.filter(
                action_flag__in=(REQUESTION_REGISTRATION, ADD_REQUESTION,
                                 REQUESTION_IMPORT),
                added_pref_sadiks=sadik).count()
            change_pref_logs = logs.filter(
                action_flag__in=(CHANGE_PREFERRED_SADIKS,
                                 CHANGE_PREFERRED_SADIKS_BY_OPERATOR))
#                при изменении указан в кач-ве приоритетного
            added_pref_number = change_pref_logs.filter(
                added_pref_sadiks=sadik).count()
#                при изменении удален из приоритетных
            removed_pref_number = change_pref_logs.filter(
                removed_pref_sadiks=sadik).count()

            total_pref_add = added_pref_number - removed_pref_number
            sadiks_info.append({'sadik_name': unicode(sadik),
                'registration_set_pref_number': registration_set_pref_number,
                'added_pref_number': added_pref_number,
                'removed_pref_number': removed_pref_number,
                'total_pref_add': total_pref_add,
                })
        areas_info.append(
            {'area_name': unicode(area), 'sadiks_info': sadiks_info})
    return {'areas_info': areas_info}

REPORTS_INFO = {
    "functions": {
        REPORT_FILLABILITY: get_fillability_report_data,
        REPORT_TRANSITIONS: get_transitions_report_data,
        REPORT_STATUSES: get_statuses_report_data,
        REPORT_SADIKS_REQUESTS: get_sadiks_requests_report_data, },
    "forms": {
        REPORT_FILLABILITY: ReportAgeGroupForm,
        REPORT_TRANSITIONS: ReportDateForm,
        REPORT_STATUSES: ReportDateForm,
        REPORT_SADIKS_REQUESTS: ReportAgeGroupForm},
    "templates": {
        REPORT_FILLABILITY: "logger/report_fillability.html",
        REPORT_TRANSITIONS: "logger/report_transitions.html",
        REPORT_STATUSES: "logger/report_statuses.html",
        REPORT_SADIKS_REQUESTS: "logger/report_sadiks_requests.html", },
    "parameters": {
        REPORT_FILLABILITY: ["age_group", ],
        REPORT_TRANSITIONS: [],
        REPORT_STATUSES: [],
        REPORT_SADIKS_REQUESTS: ["age_group", ]},
    }


class ReportsForType(OperatorPermissionMixin, TemplateView):
    u"""отображение отчетов определенного типа"""
    template_name = "logger/reports_for_type.html"

    def dispatch(self, request, report_type):
        report_type = int(report_type)
        if report_type not in dict(REPORTS_CHOICES):
            raise Http404
        return super(ReportsForType, self).dispatch(request, report_type)

    def get(self, request, report_type):
        form = REPORTS_INFO["forms"][report_type]()
        return self.render_to_response({"form": form,
            'report_type_verbose': dict(REPORTS_CHOICES)[report_type],
            "report_types": dict(REPORTS_CHOICES)})

    def post(self, request, report_type):
        form = REPORTS_INFO["forms"][report_type](request.POST)
        context = {"form": form,
            'report_type_verbose': dict(REPORTS_CHOICES)[report_type],
            "report_types": dict(REPORTS_CHOICES)}
        if form.is_valid():
            reports = Report.objects.filter(
                Q(from_date__gte=form.cleaned_data["from_date"]) |
                    Q(to_date__lte=form.cleaned_data["to_date"]),
                type=report_type,)
            if "age_group" in form.cleaned_data:
                reports = reports.filter(
                    age_group=form.cleaned_data["age_group"])
            if "decision_type" in form.cleaned_data:
                reports = reports.filter(
                    decision_type=form.cleaned_data["decision_type"])

            context.update({"reports": reports})
        return self.render_to_response(context)


class ReportShow(OperatorPermissionMixin, TemplateView):

    def dispatch(self, request, report_id):
        self.report = get_object_or_404(Report, id=report_id)
        return super(ReportShow, self).dispatch(request, report_id)

    def get_template_names(self):
        return [REPORTS_INFO["templates"][self.report.type], ]

    def get(self, *args, **kwargs):
        context = {"report": self.report, "report_types": dict(REPORTS_CHOICES)}
        context.update(self.report.get_data())
        return self.render_to_response(context)
