# -*- coding: utf-8 -*-
import json

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.forms.util import ErrorList
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView, View
from django.utils import simplejson

from sadiki.account.forms import RequestionForm, PersonalDataForm, \
    PersonalDocumentForm, BenefitsForm, ChangeRequestionForm,\
    PreferredSadikForm, SocialProfilePublicForm, EmailAddForm, \
    BasePersonalDocumentFormset
from sadiki.account.utils import get_plugin_menu_items, get_profile_additions
import sadiki.authorisation.views
from sadiki.core.exceptions import TransitionNotAllowed
from sadiki.core.models import PersonalDocument, Requestion, Benefit, \
    STATUS_REQUESTER_NOT_CONFIRMED, Area, District, \
    STATUS_REQUESTER, AgeGroup, STATUS_DISTRIBUTED, STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE, Sadik, EvidienceDocument, BENEFIT_DOCUMENT, \
    STATUS_DECISION, STATUS_ON_DISTRIBUTION, STATUS_ON_TEMP_DISTRIBUTION
from sadiki.core.permissions import RequirePermissionsMixin
from sadiki.core.utils import get_openlayers_js, get_current_distribution_year,\
    get_coords_from_address, get_random_token, find_closest_kg
from sadiki.core.workflow import REQUESTION_ADD_BY_REQUESTER, ACCOUNT_CHANGE_REQUESTION
from sadiki.core.workflow import CHANGE_PERSONAL_DATA, CHANGE_PDATA_REQUESTION
from sadiki.logger.models import Logger
from sadiki.core.views_base import GenerateBlankBase
from sadiki.logger.utils import add_special_transitions_to_requestions
from sadiki.conf_settings import USE_DISTRICTS
import sadiki.operator.forms


def get_json_sadiks_location_data():
    sadiks_location_data = {}
    for sadik in Sadik.objects.filter(active_registration=True).select_related('area__id', 'address'):
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

    @method_decorator(login_required)
    def dispatch(self, request):
        kwargs = {
            'profile': request.user.get_profile(),
            'redirect_to': reverse('frontpage'),
            'action_flag': CHANGE_PERSONAL_DATA,
        }
        return super(AccountFrontPage, self).dispatch(request, **kwargs)

    def get_context_data(self, **kwargs):
        profile = kwargs.get('profile')
        form = EmailAddForm()
        profile_change_form = SocialProfilePublicForm(instance=profile)
        pdata_form = PersonalDataForm(instance=profile)
        context = {
            'params': kwargs,
            'profile': profile,
            'form': form,
            'profile_change_form': profile_change_form,
            'pdata_form': pdata_form,
            'doc_formset': self.get_documents_formset(profile),
            'plugin_menu_items': get_plugin_menu_items(),
            'profile_additions': get_profile_additions(),
        }
        vkontakte_associations = profile.user.social_auth.filter(provider='vkontakte-oauth2')
        if vkontakte_associations:
            context.update({'vkontakte_association': vkontakte_associations[0]})
        return context

    def post(self, request, **kwargs):
        profile = kwargs.get('profile')
        redirect_to = kwargs.get('redirect_to')
        action_flag = kwargs.get('action_flag')
        old_pdata = profile.to_dict()
        context = self.get_context_data(profile=profile)
        pdata_form = PersonalDataForm(request.POST, instance=profile)
        PersonalDocumentFormset = modelformset_factory(
            PersonalDocument,
            form=PersonalDocumentForm,
            formset=BasePersonalDocumentFormset,
            extra=len(PersonalDocument.DOC_TYPE_CHOICES),
        )
        doc_formset = PersonalDocumentFormset(request.POST)
        if (pdata_form.is_valid() and doc_formset.is_valid()
                and (pdata_form.has_changed() or doc_formset.has_changed())):
            pdata_form.save()
            doc_formset.save()
            messages.success(request,
                             u'Персональные данные успешно сохранены')
            new_pdata = profile.to_dict()
            Logger.objects.create_for_action(
                action_flag,
                context_dict={'old_pdata': old_pdata,
                              'new_pdata': new_pdata},
                extra={'user': request.user, 'obj': profile},
            )
            return HttpResponseRedirect(redirect_to)
        else:
            messages.error(request, u'Персональные данные не были сохранены. '
                           u'Пожалуйста, исправьте ошибки, выделенные красным')
            context.update({'pdata_form': pdata_form,
                            'doc_formset': doc_formset})
            return self.render_to_response(context)

    def get_documents_formset(self, profile):
        choices = PersonalDocument.DOC_TYPE_CHOICES
        documents_set = profile.personaldocument_set
        initial_values = []
        for choice in choices:
            if not documents_set.filter(doc_type=choice[0]).exists():
                initial_values.append({'doc_type': choice[0],
                                       'profile': profile.id})
        PersonalDocumentFormset = modelformset_factory(
            PersonalDocument,
            form=PersonalDocumentForm,
            formset=BasePersonalDocumentFormset,
            extra=len(initial_values),
        )
        formset = PersonalDocumentFormset(initial=initial_values,
                                          queryset=documents_set.all())
        return formset


class EmailChange(AccountPermissionMixin, View):

    @method_decorator(login_required)
    def dispatch(self, request):
        profile = request.user.get_profile()
        return super(EmailChange, self).dispatch(request, profile)

    def post(self, request, profile):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        form = EmailAddForm(data=request.POST)
        if form.is_valid():
            if request.POST['email'] != profile.user.email:
                if User.objects.filter(email=request.POST['email']).exclude(username=request.user).exists():
                    form._errors['email'] = ErrorList([u'Данный почтовый адрес уже занят'])
                    return HttpResponse(content=json.dumps(
                        {'ok': False, 'errors': form.errors}),
                        mimetype='text/javascript')
                profile.user.email = request.POST['email']
                profile.user.save()
                if request.user.is_operator():
                    profile.email_verified = True
                    profile.save()
                if request.user.is_requester():
                    profile.email_verified = False
                    profile.save()
                    sadiki.authorisation.views.send_confirm_letter(request)
            return HttpResponse(content=json.dumps({'ok': True}),
                                mimetype='text/javascript')

        return HttpResponse(content=json.dumps(
            {'ok': False, 'errors': form.errors}),
            mimetype='text/javascript')


class SocialProfilePublic(AccountPermissionMixin, View):

    @method_decorator(login_required)
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
        districts_all = District.objects.all()
        return {
            'profile': kwargs.get('profile'),
            'sadiks_location_data': get_json_sadiks_location_data(),
            'plugin_menu_items': get_plugin_menu_items(),
            'areas_all': Area.objects.all().select_related('district'),
            'districts_all': districts_all,
            'use_districts': USE_DISTRICTS,
        }

    def create_profile(self):
        raise NotImplementedError()

    def redirect_to(self, requestion):
        return reverse('account_requestion_info',
                       kwargs={'requestion_id': requestion.id})

    @method_decorator(login_required)
    def dispatch(self, request):
        profile = request.user.get_profile()
        return super(RequestionAdd, self).dispatch(request, profile=profile)

    def get_documents_formset(self):
        return None

    def get(self, request, profile):
        token = get_random_token()
        if request.session.get('token'):
            request.session['token'].update({token: None})
            request.session.modified = True
        else:
            request.session['token'] = {token: None}
        context = self.get_context_data(profile=profile)
        form = self.requestion_form(initial={'token': token})
        benefits_form = self.benefits_form()
        DocumentFormset = self.get_documents_formset()
        if DocumentFormset:
            formset = DocumentFormset(
                queryset=EvidienceDocument.objects.filter(
                template__destination=BENEFIT_DOCUMENT))
        else:
            formset = None
        context.update({
            'form': form, 'benefits_form': benefits_form,
            'formset': formset, 'openlayers_js': get_openlayers_js()})
        return self.render_to_response(context)

    def post(self, request, profile):
        token_dict = request.session.get('token')
        current_request_token = request.POST.get('token')
        if not token_dict or not(current_request_token in token_dict.keys()):
            return HttpResponseRedirect(request.path)
        if token_dict[current_request_token]:
            requestion = Requestion.objects.get(
                pk=token_dict[current_request_token])
            return HttpResponseRedirect(self.redirect_to(requestion))

        context = self.get_context_data(profile=profile)
        form = self.requestion_form(request.POST)
        benefits_form = self.benefits_form(data=request.POST)
        DocumentFormset = self.get_documents_formset()
        if DocumentFormset:
            formset = DocumentFormset(
                data=request.POST,
                queryset=EvidienceDocument.objects.filter(
                    template__destination=BENEFIT_DOCUMENT))
        else:
            formset = None
        try:
            forms_valid = all((form.is_valid(), benefits_form.is_valid(),
                               (not formset or formset.is_valid())))
        except TransitionNotAllowed as e:
            messages.error(request, e.message)
            context.update({'form': form, 'benefits_form': benefits_form,
                            'formset': formset,
                            'openlayers_js': get_openlayers_js()})
            return self.render_to_response(context)

        if forms_valid:
            if not profile:
                profile = self.create_profile()
            requestion = form.save(profile=profile)
            pref_sadiks = form.cleaned_data.get('pref_sadiks')
            benefits_form.instance = requestion
            requestion = benefits_form.save()
            find_closest_kg(requestion, save=True)
            if formset:
                formset.instance = requestion
                benefit_documents = formset.save()
            else:
                benefit_documents = None
            context_dict = {
                'requestion': requestion,
                'pref_sadiks': pref_sadiks,
                'benefit_documents': benefit_documents,
                'areas': form.cleaned_data.get('areas')}
            context_dict.update(dict([(field, benefits_form.cleaned_data[field])
                                for field in benefits_form.changed_data]))
            Logger.objects.create_for_action(
                self.logger_action,
                context_dict=context_dict, extra={
                    'user': request.user, 'obj': requestion,
                    'added_pref_sadiks': pref_sadiks})
            messages.info(request,
                          u'Добавлена заявка %s' % requestion.requestion_number)
            request.session['token'][current_request_token] = requestion.id
            request.session.modified = True
            return HttpResponseRedirect(self.redirect_to(requestion))
        else:
            context.update({'form': form, 'benefits_form': benefits_form,
                            'formset': formset,
                            'openlayers_js': get_openlayers_js()})
            return self.render_to_response(context)


class RequestionInfo(AccountRequestionMixin, TemplateView):
    template_name = 'account/requestion_info.html'
    logger_action = ACCOUNT_CHANGE_REQUESTION
    logger_pdata_action = CHANGE_PDATA_REQUESTION
    change_requestion_form = ChangeRequestionForm

    def can_change_benefits(self, requestion):
        return requestion.status == STATUS_REQUESTER_NOT_CONFIRMED

    def can_change_requestion(self, requestion):
        return requestion.editable

    def redirect_to(self, requestion):
        return reverse('account_requestion_info',
                       kwargs={'requestion_id': requestion.id})

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
            'use_districts': USE_DISTRICTS,
        })
        return self.render_to_response(context)

    def post(self, request, requestion):
        context = self.get_context_data(requestion)
        change_requestion_form = self.change_requestion_form(
            request.POST, instance=requestion)
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
                Logger.objects.create_for_action(
                    self.logger_pdata_action,
                    context_dict={'requestion': requestion},
                    extra={'user': request.user, 'obj': requestion},
                )
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
                if 'location' in context_dict['changed_data']:
                    find_closest_kg(requestion, save=True)
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
            'use_districts': USE_DISTRICTS,

        })
        return self.render_to_response(context)

    def get_queue_data(self, requestion):
        before = Requestion.objects.queue().active_queue().requestions_before(requestion)
        benefits_before = before.benefits().count()
        confirmed_before = before.confirmed().count()
        requestions_before = before.count()
        benefits_after = Requestion.objects.active_queue().benefits().count() - benefits_before
        confirmed_after = Requestion.objects.active_queue().confirmed().count() - confirmed_before
        requestions_after = Requestion.objects.active_queue().count() - requestions_before
        offset = max(0, requestions_before - 20)
        queue_chunk = Requestion.objects.queue().hide_distributed().add_distributed_sadiks()[offset:requestions_before + 20]
        queue_chunk = add_special_transitions_to_requestions(queue_chunk)

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
            'areas_all': Area.objects.all(),
            'profile': requestion.profile,
            'NOT_APPEAR_STATUSES': [STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE],
            'STATUS_DISTIRIBUTED': STATUS_DISTRIBUTED,
            'STATUS_REQUESTER_NOT_CONFIRMED': STATUS_REQUESTER_NOT_CONFIRMED,
            'sadiks_location_data': get_json_sadiks_location_data(),
            'pref_sadiks_ids': pref_sadiks_ids,
            'areas_ids': simplejson.dumps([
                req for req in requestion.areas.all().values_list(
                    'id', flat=True)]),
            'can_change_benefits': self.can_change_benefits(requestion),
            'can_change_requestion': self.can_change_requestion(requestion),
            'plugin_menu_items': get_plugin_menu_items(),
        }

        context.update(kwargs)
        context.update(self.get_queue_data(requestion))
        return context


class GenerateBlank(AccountRequestionMixin, GenerateBlankBase):
    pass
