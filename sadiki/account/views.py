# -*- coding: utf-8 -*-
import json
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView, View
from django.utils import simplejson
from sadiki.account.forms import RequestionForm, \
    BenefitsForm, ChangeRequestionForm,\
    PreferredSadikForm, SocialProfilePublicForm
from sadiki.core.models import Requestion, \
    STATUS_REQUESTER_NOT_CONFIRMED, \
    STATUS_REQUESTER, AgeGroup, STATUS_DISTRIBUTED, STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE, Sadik, EvidienceDocument, BENEFIT_DOCUMENT
from sadiki.core.permissions import RequirePermissionsMixin
from sadiki.core.utils import get_openlayers_js, get_current_distribution_year
from sadiki.core.workflow import REQUESTION_ADD_BY_REQUESTER, ACCOUNT_CHANGE_REQUESTION
from sadiki.logger.models import Logger
from sadiki.core.views_base import GenerateBlankBase


def get_json_sadiks_location_data():
    sadiks_location_data = {}
    for sadik in Sadik.objects.filter(active_registration=True):
        if sadik.address.coords:
            sadiks_location_data.update({sadik.id: {
                'area_id': sadik.area.id,
                'id': sadik.id,
                'location': sadik.address.coords.tuple,
                'address': sadik.address.text,
                'phone': sadik.phone,
                'name': sadik.short_name,
                'number': sadik.number,
                'url': reverse('sadik_info', args=[sadik.id, ]),
            }})
    return simplejson.dumps(sadiks_location_data)


class AccountPermissionMixin(RequirePermissionsMixin):
    u"""
    проверка является ли пользователь оператором
    """
    required_permissions = ['is_requester']


class AccountRequestionMixin(AccountPermissionMixin):

    def check_permissions(self, request, requestion):
        if AccountPermissionMixin.check_permissions(self, request):
            return requestion.profile.user == request.user
        return False

    def dispatch(self, request, requestion_id):
        requestion = get_object_or_404(Requestion, id=requestion_id)
        return RequirePermissionsMixin.dispatch(self, request,
            requestion=requestion)


class AccountRequestionEditMixin(AccountRequestionMixin):
    def check_permissions(self, request, requestion):
        return super(AccountRequestionEditMixin, self).check_permissions(
            request, requestion) and requestion.editable


class AccountFrontPage(AccountPermissionMixin, TemplateView):
    u"""
    отображается страница личного кабинета пользователя
    """
    template_name = 'account/frontpage.html'

    def dispatch(self, request):
        profile = request.user.get_profile()
        return super(AccountFrontPage, self).dispatch(request, profile=profile)

    def get_context_data(self, **kwargs):
        profile = kwargs.get('profile')
        profile_change_form = SocialProfilePublicForm(instance=profile)
        context = {
            'params': kwargs,
            'profile': profile,
            'profile_change_form': profile_change_form
        }
        vkontakte_associations = profile.user.social_auth.filter(provider='vkontakte-oauth2')
        if vkontakte_associations:
            context.update({'vkontakte_association': vkontakte_associations[0]})
        return context


class SocialProfilePublic(AccountPermissionMixin, View):

    def dispatch(self, request):
        profile = request.user.get_profile()
        return super(SocialProfilePublic, self).dispatch(request, profile)

    def post(self, request, profile):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        form = SocialProfilePublicForm(data=request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return HttpResponse(content=json.dumps({'ok': False}),
                                mimetype='text/javascript')
        return HttpResponse(content=json.dumps({'ok': False}),
                            mimetype='text/javascript')


class RequestionAdd(AccountPermissionMixin, TemplateView):
    u"""Добавление заявки пользователем"""
    template_name = 'account/requestion_add.html'
    requestion_form = RequestionForm
    benefits_form = BenefitsForm
    logger_action = REQUESTION_ADD_BY_REQUESTER

    def get_context_data(self, **kwargs):
        return {
            'profile': kwargs.get('profile'),
            'sadiks_location_data': get_json_sadiks_location_data(),
        }

    def create_profile(self):
        raise NotImplementedError()

    def redirect_to(self, requestion):
        return reverse('account_requestion_info', kwargs={'requestion_id': requestion.id})

    def dispatch(self, request):
        profile = request.user.get_profile()
        return super(RequestionAdd, self).dispatch(request, profile=profile)

    def get_documents_formset(self):
        return None

    def get(self, request, profile):
        context = self.get_context_data(profile=profile)
        form = self.requestion_form()
        benefits_form = self.benefits_form()
        DocumentFormset = self.get_documents_formset()
        if DocumentFormset:
            formset = DocumentFormset(
                queryset=EvidienceDocument.objects.filter(
                template__destination=BENEFIT_DOCUMENT))
        else:
            formset = None
        context.update({'form': form, 'benefits_form': benefits_form,
            'formset': formset, 'openlayers_js': get_openlayers_js()})
        return self.render_to_response(context)

    def post(self, request, profile):
        context = self.get_context_data(profile=profile)
        form = self.requestion_form(request.POST)
        benefits_form = self.benefits_form(data=request.POST)
        DocumentFormset = self.get_documents_formset()
        if DocumentFormset:
            formset = DocumentFormset(data=request.POST,
                queryset=EvidienceDocument.objects.filter(
                template__destination=BENEFIT_DOCUMENT))
        else:
            formset = None
        if all((form.is_valid(), benefits_form.is_valid(), (not formset or formset.is_valid()))):
            if not profile:
                profile = self.create_profile()
            requestion = form.save(profile=profile)
            pref_sadiks = form.cleaned_data.get('pref_sadiks')
            benefits_form.instance = requestion
            requestion = benefits_form.save()
            formset.save()
            context_dict = {'requestion': requestion,
                'pref_sadiks': pref_sadiks,
                'areas': form.cleaned_data.get('areas')}
            context_dict.update(dict([(field, benefits_form.cleaned_data[field])
                for field in benefits_form.changed_data]))
            Logger.objects.create_for_action(self.logger_action,
                context_dict=context_dict, extra={
                'user': request.user, 'obj': requestion,
                'added_pref_sadiks': pref_sadiks})
            messages.info(request, u'Добавлена заявка %s' % requestion.requestion_number)
            return HttpResponseRedirect(self.redirect_to(requestion))
        else:
            context.update({'form': form, 'benefits_form': benefits_form,
                            'formset': formset, 'openlayers_js': get_openlayers_js()})
            return self.render_to_response(context)


class RequestionInfo(AccountRequestionMixin, TemplateView):
    template_name = 'account/requestion_info.html'
    logger_action = ACCOUNT_CHANGE_REQUESTION
    change_requestion_form = ChangeRequestionForm

    def can_change_benefits(self, requestion):
        return requestion.status == STATUS_REQUESTER_NOT_CONFIRMED

    def can_change_requestion(self, requestion):
        return requestion.editable

    def redirect_to(self, requestion):
        return reverse('account_requestion_info', kwargs={'requestion_id': requestion.id})

    def get_documents_formset(self):
        return None

    def get(self, request, requestion):
        context = self.get_context_data(requestion)
        change_requestion_form = self.change_requestion_form(instance=requestion)
        change_benefits_form = BenefitsForm(instance=requestion)
        pref_sadiks_form = PreferredSadikForm(instance=requestion)
        DocumentFormset = self.get_documents_formset()
        if DocumentFormset:
            formset = self.get_documents_formset()(
                instance=requestion, queryset=EvidienceDocument.objects.filter(
                template__destination=BENEFIT_DOCUMENT))
        else:
            formset = None
        context.update({
            'formset': formset,
            'change_requestion_form': change_requestion_form,
            'change_benefits_form': change_benefits_form,
            'pref_sadiks_form': pref_sadiks_form,
        })
        return self.render_to_response(context)

    def post(self, request, requestion):
        context = self.get_context_data(requestion)
        change_requestion_form = self.change_requestion_form(request.POST, instance=requestion)
        change_benefits_form = BenefitsForm(request.POST, instance=requestion)
        pref_sadiks_form = PreferredSadikForm(request.POST, instance=requestion)
        DocumentFormset = self.get_documents_formset()
        if DocumentFormset:
            formset = self.get_documents_formset()(request.POST,
                instance=requestion, queryset=EvidienceDocument.objects.filter(
                template__destination=BENEFIT_DOCUMENT))
        else:
            formset = None
        can_change_benefits = self.can_change_benefits(requestion)
        if not requestion.editable:
            messages.error(request, u'Заявка %s не может быть изменена' % requestion)
            return HttpResponseRedirect(reverse('account_requestion_info', args=[requestion.id]))
        if all((change_requestion_form.is_valid(), change_benefits_form.is_valid(),
                pref_sadiks_form.is_valid(), (not formset or formset.is_valid()))):
            context_dict = {'requestion': requestion, 'changed_data': [], 'cleaned_data': {}}
            data_changed = False
            extra = {'user': request.user, 'obj': requestion}
            if change_requestion_form.has_changed():
                data_changed = True
                change_requestion_form.save()
                context_dict['changed_data'].extend(change_requestion_form.changed_data)
                context_dict['cleaned_data'].update(change_requestion_form.cleaned_data)
            # изменение льгот возможно только для документально неподтврежденных
            if can_change_benefits:
                if change_benefits_form.has_changed():
                    data_changed = True
                    change_benefits_form.save()
                    context_dict['changed_data'].extend(change_benefits_form.changed_data)
                    context_dict['cleaned_data'].update(change_benefits_form.cleaned_data)
                if formset and formset.has_changed():
                    benefit_documents = formset.save()
                    data_changed = True
                    context_dict['cleaned_data'].update({'benefit_documents': benefit_documents})
            if pref_sadiks_form.has_changed():
                data_changed = True
                pref_sadiks = set(requestion.pref_sadiks.all())
                pref_sadiks_form.save()
                new_pref_sadiks = set(requestion.pref_sadiks.all())
                added_pref_sadiks = new_pref_sadiks - pref_sadiks
                removed_pref_sadiks = pref_sadiks - new_pref_sadiks
                context_dict['changed_data'].extend(pref_sadiks_form.changed_data)
                context_dict['cleaned_data'].update(pref_sadiks_form.cleaned_data)
                extra.update({'added_pref_sadiks': added_pref_sadiks})
                extra.update({'removed_pref_sadiks': removed_pref_sadiks})
            if data_changed:
                Logger.objects.create_for_action(self.logger_action,
                    context_dict=context_dict, extra=extra)
                messages.success(request, u'Изменения в заявке %s сохранены' % requestion)
            else:
                messages.error(request, u'Заявка %s не была изменена' % requestion)
            return HttpResponseRedirect(self.redirect_to(requestion))
        context.update({
            'formset': formset,
            'change_requestion_form': change_requestion_form,
            'change_benefits_form': change_benefits_form,
            'pref_sadiks_form': pref_sadiks_form,
            'can_change_benefits': can_change_benefits,
        })
        return self.render_to_response(context)

    def get_queue_data(self, requestion):
        before = Requestion.objects.queue().requestions_before(requestion)
        benefits_before = before.benefits().count()
        confirmed_before = before.confirmed().count()
        requestions_before = before.count()
        benefits_after = Requestion.objects.queue().benefits().count() - benefits_before
        confirmed_after = Requestion.objects.queue().confirmed().count() - confirmed_before
        requestions_after = Requestion.objects.queue().count() - requestions_before
        offset = max(0, requestions_before - 20)
        queue_chunk = Requestion.objects.queue().add_distributed_sadiks()[offset:requestions_before + 20]

        # Вычесть свою заявку
        requestions_after -= 1
        if requestion.benefit_category.priority > 0:
            benefits_after -= 1
        if requestion.status == STATUS_REQUESTER:
            confirmed_after -= 1

        # для заявок вычисляем возрастные группы
        age_groups = AgeGroup.objects.all()
        current_distribution_year = get_current_distribution_year()
        for req in queue_chunk:
            req.age_groups_calculated = req.age_groups(
                age_groups=age_groups,
                current_distribution_year=current_distribution_year)
        return {
            'benefits_before': benefits_before,
            'benefits_after': benefits_after,
            'confirmed_before': confirmed_before,
            'confirmed_after': confirmed_after,
            'requestions_before': requestions_before,
            'requestions_after': requestions_after,
            'queue': queue_chunk,
            'offset': offset,
        }

    def get_context_data(self, requestion, **kwargs):

        pref_sadiks_ids = requestion.pref_sadiks.all().values_list('id', flat=True)

        context = {
            'requestion': requestion,
            'profile': requestion.profile,
            'NOT_APPEAR_STATUSES': [STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE],
            'STATUS_DISTIRIBUTED': STATUS_DISTRIBUTED,
            'STATUS_REQUESTER_NOT_CONFIRMED': STATUS_REQUESTER_NOT_CONFIRMED,
            'sadiks_location_data': get_json_sadiks_location_data(),
            'pref_sadiks_ids': pref_sadiks_ids,
            'areas_ids': requestion.areas.all().values_list('id', flat=True),
            'can_change_benefits': self.can_change_benefits(requestion),
            'can_change_requestion': self.can_change_requestion(requestion),
        }

        context.update(kwargs)
        context.update(self.get_queue_data(requestion))
        return context


class GenerateBlank(AccountRequestionMixin, GenerateBlankBase):
    pass
