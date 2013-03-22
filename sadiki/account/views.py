# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from django.utils import simplejson
from sadiki.account.forms import ProfileChangeForm, RequestionForm, \
    ChangeRequestionForm, PreferredSadikForm, BenefitsForm, DocumentForm, BenefitCategoryForm, RequestionAddressForm
from sadiki.core.models import Profile, Requestion, \
    BENEFIT_DOCUMENT, STATUS_REQUESTER_NOT_CONFIRMED, \
    EvidienceDocument, STATUS_REQUESTER, BenefitCategory
from sadiki.core.permissions import RequirePermissionsMixin
from sadiki.core.utils import get_openlayers_js
from sadiki.core.workflow import ADD_REQUESTION, CHANGE_PROFILE, \
    CHANGE_REQUESTION, CHANGE_PREFERRED_SADIKS, CHANGE_BENEFITS
from sadiki.logger.models import Logger
from sadiki.anonym.forms import PersonalDataApproveForm
from sadiki.core.views import GenerateBlankBase


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

    def get_context_data(self, **kwargs):
        return {
            'params': kwargs,
            'profile': self.request.user.profile,
        }


class RequestionAdd(AccountPermissionMixin, TemplateView):
    u"""Добавление заявки пользователем"""
    template_name = 'account/requestion_add.html'

    def get_context_data(self, **kwargs):
        return {
            'params': kwargs,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        form = RequestionForm()
        address_form = RequestionAddressForm()
        if settings.FACILITY_STORE == settings.FACILITY_STORE_YES:
            benefits_form = BenefitsForm()
        else:
            benefits_form = BenefitCategoryForm()
        personal_data_approve_form = PersonalDataApproveForm()
        context.update({'form': form, 'address_form': address_form,
            'benefits_form': benefits_form,
            'personal_data_approve_form': personal_data_approve_form,
            'openlayers_js': get_openlayers_js()})
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        form = RequestionForm(request.POST)
        address_form = RequestionAddressForm(request.POST)
        personal_data_approve_form = PersonalDataApproveForm(request.POST)
        if settings.FACILITY_STORE == settings.FACILITY_STORE_YES:
            benefits_form = BenefitsForm(data=request.POST)
        else:
            benefits_form = BenefitCategoryForm(data=request.POST)
        if (form.is_valid() and benefits_form.is_valid() and
                address_form.is_valid() and personal_data_approve_form.is_valid()):
            profile = request.user.get_profile()
            address = address_form.save()
            requestion = form.save(profile=profile)
            requestion.address = address
            requestion.save()
            pref_sadiks = form.cleaned_data.get('pref_sadiks')
            benefits_form.instance = requestion
            requestion = benefits_form.save()
            context_dict = {'requestion': requestion,
                'pref_sadiks': pref_sadiks,
                'areas': form.cleaned_data.get('areas')}
            context_dict.update(dict([(field, benefits_form.cleaned_data[field])
                for field in benefits_form.changed_data]))
            Logger.objects.create_for_action(ADD_REQUESTION,
                context_dict=context_dict, extra={
                'user': request.user, 'obj': requestion,
                'added_pref_sadiks': pref_sadiks})
            messages.info(request, u'Добавлена заявка %s' % requestion.requestion_number)
#            если были заданы типы льгот, то редирект на изменение документов
            if (settings.FACILITY_STORE == settings.FACILITY_STORE_YES and
                requestion.benefit_category != BenefitCategory.objects.category_without_benefits()):
                return HttpResponseRedirect(reverse("account_benefits_change", kwargs={'requestion_id': requestion.id}))
    #            иначе на страницу с информацией о заявке
            return HttpResponseRedirect(
                reverse('account_requestion_info',
                         kwargs={'requestion_id': requestion.id}))
        else:
            context.update({'form': form, 'benefits_form': benefits_form,
                'address_form': address_form,
                'personal_data_approve_form': personal_data_approve_form,
                'openlayers_js': get_openlayers_js()})
            return self.render_to_response(context)


class ProfileChange(AccountPermissionMixin, TemplateView):
    u"""Изменение профиля пользователем"""
    template_name = 'account/profile_change.html'

    def dispatch(self, request):
        profile = get_object_or_404(Profile, user=request.user.pk)
        return super(ProfileChange, self).dispatch(request, profile)

    def get(self, request, profile):
        form = ProfileChangeForm(instance=profile)
        return self.render_to_response({'form': form})

    def post(self, request, profile):
        form = ProfileChangeForm(instance=profile, data=request.POST)
        if form.is_valid():
            if form.has_changed:
                profile = form.save()
#                write logs
                context_dict = {"changed_data": form.changed_data,
                    "profile": profile}
                Logger.objects.create_for_action(CHANGE_PROFILE,
                    context_dict=context_dict,
                    extra={'user': request.user, 'obj': profile})
                messages.success(request, u'Изменения в профиле сохранены')
            else:
                messages.warning(request, u'Профиль не был изменен')
            return HttpResponseRedirect(reverse('account_frontpage'))
        else:
            return self.render_to_response({'form': form})


class RequestionInfo(AccountRequestionMixin, TemplateView):
    template_name = 'account/requestion_info.html'

    def get(self, request, requestion):
        return self.render_to_response(self.get_context_data(requestion))

    def get_context_data(self, requestion, **kwargs):
        before = Requestion.objects.queue().requestions_before(requestion)
        benefits_before = before.benefits().count()
        confirmed_before = before.confirmed().count()
        requestions_before = before.count()
        benefits_after = Requestion.objects.queue().benefits().count() - benefits_before
        confirmed_after = Requestion.objects.queue().confirmed().count() - confirmed_before
        requestions_after = Requestion.objects.queue().count() - requestions_before
        queue_chunk = Requestion.objects.queue()[requestions_before - 20:requestions_before + 20]

        # Вычесть свою заявку
        requestions_after -= 1
        if requestion.benefit_category.priority > 0:
            benefits_after -= 1
        if requestion.status == STATUS_REQUESTER:
            confirmed_after -= 1

        context = {
            'requestion': requestion,
            'benefits_before': benefits_before,
            'benefits_after': benefits_after,
            'confirmed_before': confirmed_before,
            'confirmed_after': confirmed_after,
            'requestions_before': requestions_before,
            'requestions_after': requestions_after,
            'queue': queue_chunk,
            'offset': requestions_before - 20,
            'STATUS_REQUESTER_NOT_CONFIRMED': STATUS_REQUESTER_NOT_CONFIRMED,
        }

        context.update(kwargs)
        return context


class RequestionChange(AccountRequestionEditMixin, TemplateView):
    u"""Изменение заявки пользователем"""
    template_name = 'account/requestion_change.html'
    queryset = Requestion.objects.all()

    def get(self, request, requestion):
        form = ChangeRequestionForm(instance=requestion)
        address_form = RequestionAddressForm(instance=requestion.address)
        return self.render_to_response({'requestion': requestion,
            'form': form, 'address_form': address_form, 'openlayers_js': get_openlayers_js()})

    def post(self, request, requestion):
        form = ChangeRequestionForm(instance=requestion,
            data=request.POST)
        address_form = RequestionAddressForm(instance=requestion.address, data=request.POST)
        if form.is_valid() and address_form.is_valid():
            if form.has_changed() or address_form.has_changed():
                address = address_form.save()
                requestion = form.save(commit=False)
                requestion.address = address
                requestion.save()
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
                {'form': form, 'requestion': requestion, 'address_form': address_form, 'openlayers_js': get_openlayers_js()})


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
                # TODO: Добавить изящества в составление конеткста для логов
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
            formset.save()
            messages.info(request, u'''Документы были изменены''')
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
