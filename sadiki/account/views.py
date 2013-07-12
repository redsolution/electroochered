# -*- coding: utf-8 -*-
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView, View
from django.utils import simplejson
from sadiki.account.forms import RequestionForm, \
    ChangeRequestionForm, PreferredSadikForm, BenefitsForm, DocumentForm, BenefitCategoryForm, ChangeRequestionBaseForm,\
    PreferredSadikWithAreasNameForm, SocialProfilePublicForm
from sadiki.core.models import Requestion, \
    BENEFIT_DOCUMENT, STATUS_REQUESTER_NOT_CONFIRMED, \
    EvidienceDocument, STATUS_REQUESTER, AgeGroup, STATUS_DISTRIBUTED, STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE, Sadik
from sadiki.core.permissions import RequirePermissionsMixin
from sadiki.core.utils import get_openlayers_js, get_current_distribution_year
from sadiki.core.workflow import REQUESTION_ADD_BY_REQUESTER, CHANGE_REQUESTION, CHANGE_PREFERRED_SADIKS, CHANGE_BENEFITS,\
    CHANGE_DOCUMENTS, ACCOUNT_CHANGE_REQUESTION
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

    def get(self, request, profile):
        context = self.get_context_data(profile=profile)
        form = self.requestion_form()
        benefits_form = self.benefits_form()
        context.update({'form': form, 'benefits_form': benefits_form,
            'openlayers_js': get_openlayers_js()})
        return self.render_to_response(context)

    def post(self, request, profile):
        context = self.get_context_data(profile=profile)
        form = self.requestion_form(request.POST)
        benefits_form = self.benefits_form(data=request.POST)
        if (form.is_valid() and benefits_form.is_valid()):
            if not profile:
                profile = self.create_profile()
            requestion = form.save(profile=profile)
            pref_sadiks = form.cleaned_data.get('pref_sadiks')
            benefits_form.instance = requestion
            requestion = benefits_form.save()
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
                'openlayers_js': get_openlayers_js()})
            return self.render_to_response(context)


class RequestionInfo(AccountRequestionMixin, TemplateView):
    template_name = 'account/requestion_info.html'
    logger_action = ACCOUNT_CHANGE_REQUESTION

    def can_change_benefits(self, requestion):
        return requestion.status == STATUS_REQUESTER_NOT_CONFIRMED

    def redirect_to(self, requestion):
        return reverse('account_requestion_info', kwargs={'requestion_id': requestion.id})

    def get(self, request, requestion):
        context = self.get_context_data(requestion)
        change_requestion_form = ChangeRequestionBaseForm(instance=requestion)
        change_benefits_form = BenefitsForm(instance=requestion)
        pref_sadiks_form = PreferredSadikWithAreasNameForm(instance=requestion)
        context.update({
            'profile': requestion.profile,
            'change_requestion_form': change_requestion_form,
            'change_benefits_form': change_benefits_form,
            'pref_sadiks_form': pref_sadiks_form,
            'areas_ids': requestion.areas.all().values_list('id', flat=True),
            'can_change_benefits': self.can_change_benefits(requestion),
        })
        return self.render_to_response(context)

    def post(self, request, requestion):
        context = self.get_context_data(requestion)
        change_requestion_form = ChangeRequestionBaseForm(request.POST, instance=requestion)
        change_benefits_form = BenefitsForm(request.POST, instance=requestion)
        pref_sadiks_form = PreferredSadikWithAreasNameForm(request.POST, instance=requestion)
        can_change_benefits = self.can_change_benefits(requestion)
        if not requestion.editable:
            messages.error(request, u'Заявка %s не может быть изменена' % requestion)
            return HttpResponseRedirect(reverse('account_requestion_info', args=[requestion.id]))
        if all((change_requestion_form.is_valid(), change_benefits_form.is_valid(), pref_sadiks_form.is_valid())):
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

            'NOT_APPEAR_STATUSES': [STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE],
            'STATUS_DISTIRIBUTED': STATUS_DISTRIBUTED,
            'STATUS_REQUESTER_NOT_CONFIRMED': STATUS_REQUESTER_NOT_CONFIRMED,
            'sadiks_location_data': get_json_sadiks_location_data(),
            'pref_sadiks_ids': pref_sadiks_ids,
        }

        context.update(kwargs)
        context.update(self.get_queue_data(requestion))
        return context


class RequestionChange(AccountRequestionEditMixin, TemplateView):
    u"""Изменение заявки пользователем"""
    template_name = 'account/requestion_change.html'
    queryset = Requestion.objects.all()

    def get(self, request, requestion):
        form = ChangeRequestionForm(instance=requestion)
        return self.render_to_response({'requestion': requestion,
            'form': form, 'openlayers_js': get_openlayers_js()})

    def post(self, request, requestion):
        form = ChangeRequestionForm(instance=requestion,
            data=request.POST)
        if form.is_valid():
            if form.has_changed():
                requestion = form.save()
#                write logs
                context_dict = {'changed_fields': form.changed_data,
                    'requestion': requestion}
                Logger.objects.create_for_action(CHANGE_REQUESTION,
                    context_dict=context_dict,
                    extra={'user': request.user, 'obj': requestion})
                messages.success(request, u'Изменения в заявке %s сохранены' % requestion)
            else:
                messages.info(request, u'Заявка %s не была изменена' % requestion)
            return HttpResponseRedirect(
                reverse('account_requestion_info',
                        kwargs={'requestion_id': requestion.id}))
        else:
            return self.render_to_response(
                {'form': form, 'requestion': requestion, 'openlayers_js': get_openlayers_js()})


class BenefitsChange(AccountRequestionEditMixin, TemplateView):
    u"""Изменение льгот и документов для льгот"""
    template_name = 'account/requestion_benefits_change.html'

    def check_permissions(self, request, requestion):
        return (super(BenefitsChange, self).check_permissions(request, requestion) and
            requestion.status == STATUS_REQUESTER_NOT_CONFIRMED)

    def get_own_documents(self, requestion):
        serialized = []
        for obj in requestion.evidience_documents():
            serialized.append({
                'id': obj.id,
                'template': obj.template_id,
                'confirmed': obj.confirmed,
                'document_number': obj.document_number,
            })
        return simplejson.dumps(serialized)

    def get(self, request, requestion):
        benefits_form = BenefitsForm(instance=requestion)
        context = {
            'requestion': requestion,
            'benefits_form': benefits_form,
            'documents': self.get_own_documents(requestion),
            }
        return self.render_to_response(context)

    def post(self, request, requestion):
        benefits_form = BenefitsForm(
            data=request.POST,
            instance=requestion)
        if benefits_form.is_valid():
            benefits_form.save()
            context_dict = dict([(field, benefits_form.cleaned_data[field])
                for field in benefits_form.changed_data])
            context_dict.update({"requestion": requestion})
            Logger.objects.create_for_action(CHANGE_BENEFITS,
                context_dict=context_dict,
                extra={'user': request.user, 'obj': requestion})
            messages.success(request, u'Льготы для заявки %s были изменены' %
                requestion.requestion_number)
            return HttpResponseRedirect(
                reverse('account_requestion_info',
                    kwargs={'requestion_id': requestion.id}))
        else:
            return self.render_to_response({
                'requestion': requestion,
                'benefits_form': benefits_form,
                'documents': self.get_own_documents(requestion),
            })


class BenefitCategoryChange(AccountRequestionEditMixin, TemplateView):
    template_name = 'account/requestion_benefitcategory_change.html'

    def check_permissions(self, request, requestion):
        return (super(BenefitCategoryChange, self).check_permissions(request, requestion) and
            requestion.status == STATUS_REQUESTER_NOT_CONFIRMED)

    def get(self, request, requestion):
        from sadiki.account.forms import BenefitCategoryForm
        form = BenefitCategoryForm(instance=requestion)
        return self.render_to_response(
            {'requestion': requestion, 'form': form})

    def post(self, request, requestion):
        from sadiki.account.forms import BenefitCategoryForm
        form = BenefitCategoryForm(instance=requestion, data=request.POST)
        if form.is_valid():
            if form.has_changed():
                form.save()
                context_dict = {"requestion": requestion}
                Logger.objects.create_for_action(CHANGE_BENEFITS,
                    context_dict=context_dict,
                    extra={'user': request.user, 'obj': requestion})
                messages.success(
                    request, u'''Льготы для заявки %s были изменены
                         ''' % requestion.requestion_number)
            else:
                messages.success(
                    request, u'''Льготы для заявки %s не были изменены
                         ''' % requestion.requestion_number)
            return HttpResponseRedirect(
                    reverse('account_requestion_info',
                            kwargs={'requestion_id': requestion.id}))
        else:
            return self.render_to_response(
                {'requestion': requestion, 'form': form})


class PreferredSadiksChange(AccountRequestionEditMixin, TemplateView):
    u"""Изменение приоритетных ДОУ"""
    template_name = 'account/requestion_preferredsadiks_change.html'

    def get(self, request, requestion):
        form = PreferredSadikForm(instance=requestion)
        return self.render_to_response({
            'requestion': requestion,
            'form': form,
        })

    def post(self, request, requestion):
        form = PreferredSadikForm(instance=requestion, data=request.POST)
        if form.is_valid():
            if form.has_changed():
                # TODO: Добавить изящества в составление контекста для логов
                pref_sadiks = set(requestion.pref_sadiks.all())
                requestion = form.save()
                new_pref_sadiks = set(requestion.pref_sadiks.all())
                added_pref_sadiks = new_pref_sadiks - pref_sadiks
                removed_pref_sadiks = pref_sadiks - new_pref_sadiks
                context_dict = {
                    'changed_data': form.changed_data,
                    'pref_sadiks': requestion.pref_sadiks.all(),
                    'distribute_in_any_sadik': requestion.distribute_in_any_sadik}
                Logger.objects.create_for_action(CHANGE_PREFERRED_SADIKS,
                    context_dict=context_dict,
                    extra={'user': request.user, 'obj': requestion,
                        'added_pref_sadiks': added_pref_sadiks,
                        'removed_pref_sadiks': removed_pref_sadiks})
                messages.info(request, u'''
                     Приоритетные ДОУ для заявки %s изменены
                     ''' % requestion.requestion_number)
            else:
                messages.info(request, u'''Приоритетные ДОУ не были изменены''')
            return HttpResponseRedirect(
                reverse('account_requestion_info',
                        kwargs={'requestion_id': requestion.id}))
        return self.render_to_response({
            'requestion': requestion,
            'form': form,
        })


class DocumentsChange(AccountRequestionMixin, TemplateView):
    u"""Управление документами"""
    template_name = 'account/requestion_documents_change.html'

    def check_permissions(self, request, requestion):
        return (super(DocumentsChange, self).check_permissions(request, requestion) and
            requestion.status == STATUS_REQUESTER_NOT_CONFIRMED)

    def get(self, request, requestion):
        DocumentFormset = generic_inlineformset_factory(EvidienceDocument,
            form=DocumentForm, exclude=['confirmed', ], extra=1)
#        нужны только документы для льгот
        formset = DocumentFormset(
            instance=requestion, queryset=EvidienceDocument.objects.filter(
            template__destination=BENEFIT_DOCUMENT))
        return self.render_to_response({
            'formset': formset,
            'requestion': requestion,
            'confirmed': EvidienceDocument.objects.documents_for_object(
                requestion).confirmed(),
        })

    def post(self, request, requestion):
        DocumentFormset = generic_inlineformset_factory(EvidienceDocument,
            form=DocumentForm, exclude=['confirmed', ], extra=1)

        formset = DocumentFormset(request.POST,
            instance=requestion, queryset=EvidienceDocument.objects.filter(
            template__destination=BENEFIT_DOCUMENT))

        if formset.is_valid():
            if formset.has_changed():
                formset.save()
                messages.info(request, u'''Документы были изменены''')
                Logger.objects.create_for_action(
                        CHANGE_DOCUMENTS,
                        context_dict={'benefit_documents': requestion.evidience_documents().filter(
                            template__destination=BENEFIT_DOCUMENT)},
                        extra={'user': request.user, 'obj': requestion})
            else:
                messages.info(request, u'''Документы не были изменены''')
            return HttpResponseRedirect(reverse('account_requestion_info',
                    kwargs={'requestion_id': requestion.id}))
        else:
            return self.render_to_response({
                'formset': formset,
                'requestion': requestion,
                'confirmed': requestion.evidience_documents().confirmed(),
            })


class GenerateBlank(AccountRequestionMixin, GenerateBlankBase):
    pass
