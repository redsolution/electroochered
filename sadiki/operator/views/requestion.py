# -*- coding: utf-8 -*-
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.template import TemplateDoesNotExist, loader
from django.template.response import TemplateResponse
from django.utils.http import urlquote
from django.views.generic import TemplateView, View
from sadiki.account.views import SocialProfilePublic as AccountSocialProfilePublic, \
    RequestionAdd as AccountRequestionAdd, EmailChange as AccountEmailChange, \
    RequestionInfo as AccountRequestionInfo,get_json_sadiks_location_data, AccountFrontPage
from sadiki.anonym.views import Queue as AnonymQueue, \
    RequestionSearch as AnonymRequestionSearch
from sadiki.core.models import Requestion, \
    REQUESTION_IDENTITY, BenefitCategory, Profile, REQUESTION_TYPE_IMPORTED, STATUS_ON_DISTRIBUTION, EvidienceDocument
from sadiki.core.permissions import RequirePermissionsMixin, \
    REQUESTER_PERMISSION
from sadiki.core.signals import post_status_change, pre_status_change
from sadiki.core.utils import check_url, get_unique_username, get_coords_from_address, \
    create_xls_from_queue
from sadiki.core.workflow import REQUESTION_REGISTRATION_BY_OPERATOR, \
    CHANGE_REQUESTION_BY_OPERATOR, Transition, workflow, CREATE_PROFILE,\
    CHANGE_DOCUMENTS_BY_OPERATOR, CHANGE_REQUESTION_LOCATION
from sadiki.logger.models import Logger
from sadiki.operator.forms import OperatorRequestionForm, OperatorSearchForm, \
    RequestionIdentityDocumentForm, \
    ProfileSearchForm, BaseConfirmationForm, HiddenConfirmation, ChangeLocationForm, \
    OperatorChangeRequestionForm, CustomGenericInlineFormSet, DocumentForm
from sadiki.operator.plugins import get_operator_plugin_menu_items, get_operator_profile_additions
from sadiki.operator.views.base import OperatorPermissionMixin, \
    OperatorRequestionMixin, OperatorRequestionEditMixin, \
    OperatorRequestionCheckIdentityMixin
from django.forms.models import ModelFormMetaclass
from sadiki.core.views_base import GenerateBlankBase, generate_pdf
from sadiki.operator.forms import ConfirmationForm, QueueOperatorFilterForm
from sadiki.core.templatetags.sadiki_core_tags import FakeWSGIRequest


class FrontPage(OperatorPermissionMixin, TemplateView):
    u"""
    отображается страница рабочего места оператора
    """
    template_name = 'operator/frontpage.html'


class Queue(OperatorPermissionMixin, AnonymQueue):
    u"""Отображение очереди в район для оператора"""
    template_name = 'operator/queue.html'
    form = QueueOperatorFilterForm
    def get(self, *args, **kwds):
        u"""
        ``get`` переопределен для того, чтобы если заявка не нашлась по номеру
        из-за того, что выставлены параметры фильтра, которые её скрывают,
        автоматически перенаправлять на страницу безо всяких фильтров
        """
        request = args[0]
        if request.GET.get('type') == 'xls':
            response = HttpResponse(mimetype='application/vnd.ms-excel')
            queryset, form = self.process_filter_form(self.queryset, request.GET)
            num = queryset.count()
            if num < 5000:
                create_xls_from_queue(response, queryset)
                return response
            else:
                path = request.get_full_path().replace('&type=xls', '')
                messages.error(
                    request,
                    u"""Фильтр вернул {} заявок, экспорт невозможен.
                    Для корректной работы экспорта количество отфильтрованных
                    заявок не должно превышать 5000.
                    """.format(num))
                return HttpResponseRedirect(path)

        return super(Queue, self).get(*args, **kwds)


class Registration(OperatorPermissionMixin, AccountRequestionAdd):
    u"""
    одновременная регистрация пользователя и заявки для оператора
    """
    template_name = 'operator/registration.html'

    requestion_form = OperatorRequestionForm
    logger_action = REQUESTION_REGISTRATION_BY_OPERATOR

    def redirect_to(self, requestion):
        return reverse('operator_requestion_info', kwargs={'requestion_id': requestion.id})

    def get_documents_formset(self):
        return generic_inlineformset_factory(EvidienceDocument,
            formset=CustomGenericInlineFormSet,
            form=DocumentForm, fields=('template', 'document_number', ), extra=1)

    def dispatch(self, request, profile_id=None):
        if profile_id:
            profile = get_object_or_404(Profile, id=profile_id)
            if not profile.user.is_requester():
                raise Http404
        else:
            profile = None
        return super(AccountRequestionAdd, self).dispatch(request, profile)

    def create_profile(self):
        user = User.objects.create_user(username=get_unique_username())
        #        задаем права
        permission = Permission.objects.get(codename=u'is_requester')
        user.user_permissions.add(permission)
        user.set_username_by_id()
        user.save()
        return Profile.objects.create(user=user)


class RequestionAdd(Registration):
    template_name = "operator/requestion_add.html"

    def get_context_data(self, **kwargs):
        context = super(RequestionAdd, self).get_context_data(**kwargs)

        context['plugin_menu_items'] = get_operator_plugin_menu_items(context['profile'].id)

        return context


class RequestionSearch(OperatorPermissionMixin, AnonymRequestionSearch):
    u"""
    поиск заявок для оператора
    """
    template_name = 'operator/requestion_search.html'
    form = OperatorSearchForm
    initial_query = Requestion.objects.all()
    field_weights = {
        'requestion_number__exact': 0,
        'birth_date__exact': 6,
        'registration_datetime__range': 2,
        'number_in_old_list__exact': 1,
        'id__in': 5,
        'name__icontains': 3,
        }

    def guess_more(self, initial_query):
        u"""
        попробуем угадать, какой запрос принесет больше успеха,
        в случае если не найдено ни одной заявки.
        Убираем самый легковесный параметр
        """
        # необходимо минимум
        if len(initial_query) >= 2:
            new_query = initial_query.copy()
            for _ in initial_query.keys():
                lightest_key = min(new_query.keys(), key=lambda x: self.field_weights[x])
                del new_query[lightest_key]
                more_results = Requestion.objects.queue().filter(**new_query)
                if more_results:
                    return new_query, more_results


class ProfileInfo(OperatorPermissionMixin, AccountFrontPage):
    template_name = "operator/profile_info.html"

    def dispatch(self, request, profile_id):
        profile = get_object_or_404(Profile, id=profile_id)
        return super(AccountFrontPage, self).dispatch(request, profile=profile)

    def get_context_data(self, **kwargs):
        context = super(ProfileInfo, self).get_context_data(**kwargs)
        context.update(
            {'reset_password_form': HiddenConfirmation(initial={'action': 'reset_password'}),
             'plugin_menu_items': get_operator_plugin_menu_items(context['profile'].id),
             'profile_additions': get_operator_profile_additions(), })
        return context


class RequestionInfo(OperatorRequestionMixin, AccountRequestionInfo):
    template_name = "operator/requestion_info.html"
    logger_action = CHANGE_REQUESTION_BY_OPERATOR
    change_requestion_form = OperatorChangeRequestionForm

    def redirect_to(self, requestion):
        return reverse('operator_requestion_info', kwargs={'requestion_id': requestion.id})

    def get_queue_data(self, requestion):
        return {}

    def get_documents_formset(self):
        return generic_inlineformset_factory(EvidienceDocument,
            formset=CustomGenericInlineFormSet,
            form=DocumentForm, fields=('template', 'document_number', ), extra=1)

    def can_change_benefits(self, requestion):
        return self.can_change_requestion(requestion)

    def can_change_requestion(self, requestion):
        return requestion.editable and not requestion.is_fake_identity_documents

    def get_context_data(self, requestion, **kwargs):
        context = super(RequestionInfo, self).get_context_data(requestion, **kwargs)

        context['plugin_menu_items'] = get_operator_plugin_menu_items(context['profile'].id)

        return context


class SetIdentityDocument(OperatorRequestionMixin, TemplateView):
    required_permissions = ["is_operator", "is_supervisor"]
    template_name = u"operator/set_identity_document.html"

    def dispatch(self, request, requestion_id):
        redirect_to = request.REQUEST.get('next', '')
        self.redirect_to = check_url(redirect_to,
            reverse('operator_requestion_info',
                    kwargs={'requestion_id': requestion_id}))
        return super(SetIdentityDocument, self).dispatch(request, requestion_id)

    def check_permissions(self, request, requestion):
        return (requestion.evidience_documents().filter(fake=True,
                template__destination=REQUESTION_IDENTITY) and
            super(SetIdentityDocument, self).check_permissions(
                request, requestion))

    def get(self, request, requestion):
        form = RequestionIdentityDocumentForm(instance=requestion)
        return self.render_to_response(
            {'form': form, 'requestion': requestion,
                'redirect_to': self.redirect_to})

    def post(self, request, requestion):
        form = RequestionIdentityDocumentForm(instance=requestion,
            data=request.POST)
        if form.is_valid():
            form.save()
            # после указания документа можно удалить временный
            requestion.evidience_documents().filter(fake=True).delete()
            messages.info(request, u'Для заявки был указан идентифицирующий документ.')
            Logger.objects.create_for_action(
                CHANGE_DOCUMENTS_BY_OPERATOR,
                context_dict={'requestion_documents': requestion.evidience_documents().filter(
                    template__destination=REQUESTION_IDENTITY)},
                extra={'user': request.user, 'obj': requestion})
            return HttpResponseRedirect(self.redirect_to)
        return self.render_to_response({'form': form, 'requestion': requestion,
            'redirect_to': self.redirect_to})


# -----------------------------
#  Изменение статуса заявки
# -----------------------------
class RequestionStatusChange(RequirePermissionsMixin, TemplateView):
    template_name = 'operator/requestion_status_change.html'

    def check_permissions(self, request, requestion):
        # Ограничение прав для пользователя
        if request.user.is_authenticated():
            if request.user.is_requester():
                if requestion.profile.user != request.user:
                    return False

            if not self.required_permissions:
                # Если права пустые, значит переход системный (автоматический),
                # пользователь не может его инициировать
                return False
            else:
                # Преопределена проверка прав, чтобы одно и то же действие
                # могли выплонять разные роли.
                # В оригинальном CheckPermissions вместо ``any`` делается проверка на ``all``
                permission_granted = any([request.user.has_perm("auth.%s" % req)
                        for req in self.required_permissions])

            # Проверка дополнительных условий, заданных в callback
            if self.transition:
                if callable(self.transition.permission_cb):
                    if request.method == 'POST':
                        form = self.get_confirm_form(self.transition.index,
                            requestion=requestion, data=request.POST)
                        if form.is_valid():
                            cb_result = self.transition.permission_cb(
                                request.user, requestion, self.transition, request=request, form=form)
                            return cb_result and permission_granted
                    else:
                        cb_result = self.transition.permission_cb(
                            request.user, requestion, self.transition, request=request, form=None)
                        return cb_result and permission_granted
                return permission_granted

        return False

    def default_redirect_to(self, requestion):
        return reverse('operator_requestion_info', args=[requestion.id])

    def dispatch(self, request, requestion_id, dst_status):
        u"""
        Метод переопределен, чтобы сохранить в атрибутах ``transition``
        """
        requestion = get_object_or_404(Requestion, id=requestion_id)

        redirect_to = request.REQUEST.get('next', '')
        self.redirect_to = check_url(redirect_to, self.default_redirect_to(requestion))

        transition_indexes = workflow.available_transitions(src=requestion.status, dst=int(dst_status))
        if transition_indexes:
            self.transition = workflow.get_transition_by_index(transition_indexes[0])
        else:
            self.transition = None

        # копирование ролей из workflow в проверку прав
        if self.transition:
            # Если на перевод есть права
            if self.transition.required_permissions:
                temp_copy = self.transition.required_permissions[:]
                # Пропустить публичный доступ ``ANONYMOUS_PERMISSION``
                if Transition.ANONYMOUS_PERMISSION in temp_copy:
                    temp_copy.remove(Transition.ANONYMOUS_PERMISSION)
                self.required_permissions = temp_copy

            # Если переод только внутрисистемный, запретить его выполнение
            else:
                self.required_permissions = None

            #задаем шаблон в зависимости от типа изменения статуса
            self.template_name = self.get_custom_template_name() or self.template_name

        response = super(RequestionStatusChange, self).dispatch(request, requestion)
        # если проверка прав прошла успешно, переход предполагает проверку документов и
        # у заявки не указан документ, то перенаправляем на страницу указания документа
        if (isinstance(response, TemplateResponse) and not isinstance(request, FakeWSGIRequest) and
                self.transition and self.transition.check_document and requestion.is_fake_identity_documents):
            return HttpResponseRedirect(
                u'%s?next=%s' %
                (reverse('operator_requestion_set_identity_document',
                    kwargs={'requestion_id': requestion_id}),
                    urlquote(request.get_full_path()))
                )
        return response

    def get_confirm_form(self, transition_index, requestion=None, data=None,
            initial=None):
        form_class = self.transition.confirmation_form_class
        if not form_class:
            form_class = ConfirmationForm
        if isinstance(form_class, ModelFormMetaclass):
            form = form_class(
                requestion=requestion, data=data, initial=initial)
        else:
            form = form_class(requestion=requestion, data=data, initial=initial)
        return form

    def get_context_data(self, requestion, **kwargs):
        form = self.get_confirm_form(self.transition.index,
            requestion=requestion,
            initial={'transition': self.transition.index})
        return {
            'form': form,
            'transition': self.transition,
        }

    def get_custom_template_name(self):
        try:
            template = loader.get_template('operator/status_change/%s.html' % self.transition.index)
            return template.name
        except TemplateDoesNotExist:
            return None

    def get(self, request, requestion, *args, **kwargs):
        context = self.get_context_data(requestion)
        context.update({
            'requestion': requestion,
            'redirect_to': self.redirect_to
        })
        return self.render_to_response(context)

    def post(self, request, requestion, *args, **kwargs):
        if request.POST.get('confirmation') == "no":
            messages.info(request, u"Статус заявки не был изменен")
            return HttpResponseRedirect(self.redirect_to)
        context = self.get_context_data(requestion)
        form = self.get_confirm_form(self.transition.index,
            requestion=requestion, data=request.POST,
            initial={'transition': self.transition.index})
        context.update({
            'form': form,
            'requestion': requestion,
            'redirect_to': self.redirect_to
        })

        if form.is_valid():
            pre_status_change.send(sender=Requestion, request=request,
                requestion=requestion, transition=self.transition, form=form)

            # Момент истины
#            если ModelForm, то сохраняем
            if isinstance(form.__class__, ModelFormMetaclass):
                requestion = form.save(commit=False)
                requestion.status = self.transition.dst
                requestion.save()
                form.save_m2m()
            else:
                requestion.status = self.transition.dst
                requestion.save()

            post_status_change.send(sender=Requestion, request=request,
                requestion=requestion, transition=self.transition, form=form)
            return HttpResponseRedirect(self.redirect_to)
        else:
            return self.render_to_response(context)


class FindProfileForRequestion(OperatorRequestionCheckIdentityMixin,
        OperatorRequestionEditMixin, AnonymRequestionSearch):
    template_name = "operator/find_profile_for_requestion.html"
    initial_query = Profile.objects.filter(
        user__user_permissions__codename=REQUESTER_PERMISSION[0])
    form = ProfileSearchForm
    field_weights = {
        'user__username__exact': 3,
        'requestion__requestion_number__exact': 5,
        'first_name__icontains': 1,
    }

    def get_context_data(self, **kwargs):
        requestion = kwargs.get('requestion')
        return {
            'params': kwargs,
            'requestion': kwargs.get('requestion'),
            'form': self.form(),
            'profile': requestion.profile,
        }


class EmbedRequestionToProfile(OperatorRequestionCheckIdentityMixin,
        OperatorRequestionEditMixin, TemplateView):
    template_name = u"operator/embed_requestion_to_profile.html"

    def get_context_data(self, **kwargs):
        requestion = kwargs.get('requestion')
        return {
            'requestion': requestion,
            'params': kwargs,
            'profile': requestion.profile,
        }

    def check_permissions(self, request, requestion, profile):
        if super(EmbedRequestionToProfile, self).check_permissions(
                request, requestion, profile) and profile.user.is_requester()\
                and requestion.profile != profile:
            return True
        return False

    def dispatch(self, request, requestion_id, profile_id):
        profile = get_object_or_404(Profile, id=profile_id)
        return super(EmbedRequestionToProfile, self).dispatch(
            request, requestion_id=requestion_id, profile=profile)

    def get(self, request, requestion, profile):
        form = BaseConfirmationForm()
        context = self.get_context_data(
            requestion=requestion, profile=profile)
        context.update({'form': form})
        return self.render_to_response(context)

    def post(self, request, requestion, profile):

        form = BaseConfirmationForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data.get('reason')
            requestion.embed_requestion_to_profile(
                profile, request.user, reason)
            messages.info(request, u'Заявка %s была прикреплена к профилю' %
                    requestion.requestion_number)
            return HttpResponseRedirect(
                reverse("operator_requestion_info",
                    kwargs={'requestion_id': requestion.id}))
        context = self.get_context_data(requestion=requestion, profile=profile)
        context.update({'form': form})
        return self.render_to_response(context)


class GenerateBlank(OperatorRequestionMixin, GenerateBlankBase):
    templates_by_type = {
        'registration': u"operator/blanks/registration.html",
        'change_info': u"operator/blanks/change_info.html",
        'change_preferred_sadiks': u"operator/blanks/change_preferred_sadiks.html",
        'remove_registration': u"operator/blanks/remove_registration.html",
        }


class GenerateProfilePassword(OperatorPermissionMixin, View):

    def post(self, request, profile_id):
        profile = get_object_or_404(Profile, id=profile_id)
        user = profile.user
        form = HiddenConfirmation(request.POST)
        if form.is_valid() and form.cleaned_data.get('action') == 'reset_password':
            password = User.objects.make_random_password()
            user.set_password(password)
            user.save()
            result = generate_pdf(template_name='operator/blanks/reset_password.html',
                                  context_dict={'password': password, 'media_root': settings.MEDIA_ROOT,
                                                'profile': profile})
            response = HttpResponse(result.getvalue(), mimetype='application/pdf')
            return response


class ConfirmEmail(OperatorPermissionMixin, View):

    def get(self, request, profile_id):
        profile = Profile.objects.get(pk=profile_id)
        profile.email_verified = True
        profile.save()
        return HttpResponse()


class ChangeRequestionLocation(OperatorPermissionMixin, View):

    def post(self, request, requestion_id):
        requestion = get_object_or_404(Requestion, id=requestion_id)
        if not requestion.location_not_verified or requestion.status != STATUS_ON_DISTRIBUTION:
            raise Http404
        if request.is_ajax():
            location_form = ChangeLocationForm(instance=requestion, data=request.POST)
            if location_form.is_valid():
                if location_form.has_changed():
                    location_form.save()
                    Logger.objects.create_for_action(CHANGE_REQUESTION_LOCATION,
                        context_dict={'changed_fields': location_form.changed_data,
                    'requestion': requestion},
                        extra={'user': request.user, 'obj': requestion})
                return HttpResponse(content=json.dumps({'ok': True}),
                        mimetype='text/javascript')
            return HttpResponse(content=json.dumps({'ok': False}),
                        mimetype='text/javascript')

        else:
            return HttpResponseBadRequest()


class SocialProfilePublic(OperatorPermissionMixin, AccountSocialProfilePublic):

    def dispatch(self, request, profile_id):
        profile = get_object_or_404(Profile, id=profile_id)
        return super(AccountSocialProfilePublic, self).dispatch(request, profile)


class EmailChange(OperatorPermissionMixin, AccountEmailChange):

    def dispatch(self, request, profile_id):
        profile = get_object_or_404(Profile, id=profile_id)
        return super(AccountEmailChange, self).dispatch(request, profile)
