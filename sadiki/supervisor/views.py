# -*- coding: utf-8 -*-
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.formats import date_format
from django.views.generic.base import TemplateView
from sadiki.core.models import Requestion, STATUS_REQUESTER, SadikGroup, \
    Distribution, STATUS_NOT_APPEAR, STATUS_ABSENT, STATUS_ABSENT_EXPIRE, \
    STATUS_NOT_APPEAR_EXPIRE, STATUS_REMOVE_REGISTRATION, STATUS_DECISION
from sadiki.core.permissions import SUPERVISOR_PERMISSION, \
    RequirePermissionsMixin
from sadiki.core.utils import get_current_distribution_year, \
    get_distribution_year, check_url
from sadiki.core.workflow import CHANGE_REGISTRATION_DATETIME, CHANGE_BIRTHDATE, \
    ABSENT_REMOVE_REGISTRATION, \
    DECISION_REQUESTER, START_NEW_YEAR
from sadiki.logger.models import Logger
from sadiki.operator.forms import BaseConfirmationForm
from sadiki.operator.views.requestion import RequestionSearch as OperatorRequestionSearch, \
    RequestionInfo as OperatorRequestionInfo, RequestionStatusChange as OperatorRequestionStatusChange

from sadiki.supervisor.forms import RegistrationDateTimeForm, BirthDateForm


class SupervisorBases(RequirePermissionsMixin, TemplateView):
    required_permissions = [SUPERVISOR_PERMISSION[0], ]


class FrontPage(SupervisorBases):
    template_name = 'supervisor/frontpage.html'


class RequestionSearch(OperatorRequestionSearch):
    template_name = "supervisor/requestion_search.html"
    required_permissions = [SUPERVISOR_PERMISSION[0], ]


class RequestionInfo(OperatorRequestionInfo):
    template_name = "supervisor/requestion_info.html"
    required_permissions = [SUPERVISOR_PERMISSION[0], ]

    def can_change_benefits(self, requestion):
        return False

    def can_change_requestion(self, requestion):
        return False


class ChangeRegistrationDateTime(SupervisorBases):
    template_name = "supervisor/change_registration_datetime.html"

    def check_permissions(self, request, requestion):
        return (SupervisorBases.check_permissions(self, request, requestion)
                and requestion.editable)

    def dispatch(self, request, requestion_id):
        requestion = get_object_or_404(Requestion, id=requestion_id)
        return super(ChangeRegistrationDateTime, self).dispatch(
            request, requestion)

    def get(self, request, requestion):
        form = RegistrationDateTimeForm(instance=requestion)
        confirmation_form = BaseConfirmationForm()
        return self.render_to_response({
            'form': form, 'confirmation_form': confirmation_form,
            'requestion': requestion})

    def post(self, request, requestion):
        form = RegistrationDateTimeForm(instance=requestion, data=request.POST)
        confirmation_form = BaseConfirmationForm(data=request.POST)
        if form.is_valid() and confirmation_form.is_valid():
            if form.has_changed():
                requestion = form.save()
                messages.info(
                    request, u'Дата регистрации была изменена на {}'.format(
                        date_format(requestion.registration_datetime,
                                    "SHORT_DATETIME_FORMAT")))
                context_dict = {
                    'registration_datetime': requestion.registration_datetime}
                Logger.objects.create_for_action(
                    CHANGE_REGISTRATION_DATETIME, context_dict=context_dict,
                    extra={'user': request.user, 'obj': requestion},
                    reason=confirmation_form.cleaned_data.get('reason'))
            else:
                msg = u'Дата регистрации заявки {} осталась без изменений'
                messages.info(request, msg.format(requestion.requestion_number))
            return HttpResponseRedirect(
                reverse('supervisor_requestion_info',
                        kwargs={'requestion_id': requestion.id}))
        else:
            return self.render_to_response({
                'form': form, 'requestion': requestion,
                'confirmation_form': confirmation_form})


class ChangeBirthDate(SupervisorBases):
    template_name = "supervisor/change_birth_date.html"

    def check_permissions(self, request, requestion):
        return (SupervisorBases.check_permissions(self, request, requestion)
                and requestion.editable)

    def dispatch(self, request, requestion_id):
        requestion = get_object_or_404(Requestion, id=requestion_id)
        return super(ChangeBirthDate, self).dispatch(request, requestion)

    def get(self, request, requestion):
        form = BirthDateForm(instance=requestion)
        confirmation_form = BaseConfirmationForm()
        return self.render_to_response({
            'form': form, 'requestion': requestion,
            'confirmation_form': confirmation_form})

    def post(self, request, requestion):
        form = BirthDateForm(instance=requestion, data=request.POST)
        confirmation_form = BaseConfirmationForm(data=request.POST)
        if form.is_valid() and confirmation_form.is_valid():
            if form.has_changed():
                requestion = form.save()
                messages.info(
                    request, u'Дата рождения заявки {} была изменена'.format(
                        requestion.requestion_number))
                context_dict = {'birth_date': requestion.birth_date}
                Logger.objects.create_for_action(
                    CHANGE_BIRTHDATE,
                    context_dict=context_dict,
                    extra={'user': request.user, 'obj': requestion},
                    reason=confirmation_form.cleaned_data.get('reason'))
            else:
                msg = u'Дата рождения заявки {} осталась без изменений'
                messages.info(request, msg.format(requestion.requestion_number))
            return HttpResponseRedirect(reverse(
                'supervisor_requestion_info',
                kwargs={'requestion_id': requestion.id}))
        return self.render_to_response({
            'form': form, 'requestion': requestion,
            'confirmation_form': confirmation_form})


class DistributionYearInfo(SupervisorBases):
    template_name = u"supervisor/distribution_year_info.html"

    def get_context_data(self, **kwargs):
        context = super(DistributionYearInfo, self).get_context_data(**kwargs)
        context.update({
            'current_distribution_year': get_current_distribution_year(),
            'not_distributed_requestions_number':
                Requestion.objects.enrollment_in_progress().count()})
        return context


class StartDistributionYear(SupervisorBases):
    template_name = "supervisor/start_distribution_year.html"

    def check_permissions(self, request, *args, **kwargs):
        # проверяем, что начался новый год и нет распределений
        return (super(StartDistributionYear, self).check_permissions(
            request, *args, **kwargs) and
            get_current_distribution_year() != get_distribution_year() and
            not Distribution.objects.active())
            # раскомментировать, чтобы новый год не начинался с активными заявками
            # and not Requestion.objects.enrollment_in_progress().exists())

    def dispatch(self, request):
        redirect_to = request.GET.get('next') or request.POST.get('next', '')
        redirect_to = check_url(redirect_to, reverse('supervisor_frontpage'))
        return RequirePermissionsMixin.dispatch(self, request,
                                                redirect_to=redirect_to)

    @transaction.atomic
    def post(self, request, redirect_to=None):
        if request.POST.get('confirmation') == 'yes':
            # закрываем все возрастные группы на текущий год
            SadikGroup.objects.active().update(active=False)
            transaction.commit()
            Logger.objects.create_for_action(
                START_NEW_YEAR,
                context_dict={},
                extra={'user': request.user, 'obj': None})
            transaction.commit()
        return HttpResponseRedirect(redirect_to)


class RequestionStatusChange(OperatorRequestionStatusChange):
    template_name = "supervisor/requestion_status_change.html"

    def default_redirect_to(self, request, requestion):
        if request.user.is_authenticated() and request.user.is_supervisor():
            return reverse('supervisor_requestion_info', args=[requestion.id])
        return reverse('frontpage')
