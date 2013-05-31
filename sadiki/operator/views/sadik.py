# -*- coding: utf-8 -*-
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from ordereddict import OrderedDict
from sadiki.core.models import Distribution, Sadik, SadikGroup, STATUS_DECISION, \
    STATUS_ABSENT, STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE, STATUS_ABSENT_EXPIRE, \
    DISTRIBUTION_STATUS_START, Requestion, STATUS_REQUESTER, STATUS_DISTRIBUTED, \
    STATUS_REMOVE_REGISTRATION
from sadiki.core.permissions import RequirePermissionsMixin
from sadiki.core.utils import get_openlayers_js, get_current_distribution_year
from sadiki.core.workflow import CHANGE_SADIK_GROUP_PLACES, CHANGE_SADIK_INFO
from sadiki.logger.models import Logger
from sadiki.operator.forms import get_sadik_group_form, SadikForm, ChangeSadikForm, BaseSadikGroupFormSet


class SadikOperatorPermissionMixin(RequirePermissionsMixin):
    required_permissions = ['is_sadik_operator']


class SadikOperatorSadikMixin(SadikOperatorPermissionMixin):

    def check_permissions(self, request, sadik):
#        у оператора должны быть права или на ДОУ или на область
        return (super(SadikOperatorSadikMixin, self).check_permissions(request, sadik)
            and request.user.get_profile().sadik_available(sadik))

    def dispatch(self, request, sadik_id):
        sadik = get_object_or_404(Sadik, id=sadik_id)
        return super(SadikOperatorSadikMixin, self).dispatch(request, sadik)


class SadikListWithGroups(SadikOperatorPermissionMixin, TemplateView):
    u"""для текущего распределения отображение списка ДОУ"""
    template_name = 'operator/sadik_list_with_groups.html'

    def get(self, request):
        distribution = Distribution.objects.active()
        context = {'distribution': distribution}
        profile = request.user.get_profile()
#        получаем все ДОУ у которых есть возможность участвовать в распределении
        sadiks = Sadik.objects.filter_for_profile(profile)
        sadiks_dict = sadiks.add_related_groups()
        context.update({'sadiks': sadiks,
                        'area': profile.area})
        return self.render_to_response(context)


class SadikInfoChange(SadikOperatorSadikMixin, TemplateView):
    u"""изменение информации о ДОУ"""
    template_name = "operator/sadik_info_change.html"

    def get(self, request, sadik):
        form = ChangeSadikForm(instance=sadik)
        return self.render_to_response({'form': form, 'sadik': sadik,
            'openlayers_js': get_openlayers_js()})

    def post(self, request, sadik):
        form = ChangeSadikForm(data=request.POST, files=request.FILES, instance=sadik)
        if form.is_valid():
            if form.has_changed():
                form.save()
                context_dict = {'sadik': sadik,
                              'cleaned_data': form.cleaned_data,
                              'changed_data': form.changed_data, }
                Logger.objects.create_for_action(CHANGE_SADIK_INFO,
                    context_dict=context_dict,
                    extra={'user': request.user, 'obj': sadik})
                messages.success(request, u'Информация о %s изменена' % sadik)
            else:
                messages.success(request, u'Информация о %s не была изменена' % sadik)
            return HttpResponseRedirect(reverse('sadik_info',
                kwargs={'sadik_id': sadik.id}))
        return self.render_to_response({'form': form, 'sadik': sadik,
             'openlayers_js': get_openlayers_js()})


class SadikGroupChangePlaces(SadikOperatorSadikMixin, TemplateView):
    u"""задаем группы и кол-во мест в них для ДОУ"""
    template_name = 'operator/sadikgroup_change_places.html'

    def check_permissions(self, request, sadik):
#        не должно быть активных распределений
#        садик имеет возможность учавствовать в распределении
        return (
            super(SadikGroupChangePlaces, self).check_permissions(request, sadik)
            and sadik.active_distribution == True and not Distribution.objects.active())

    def create_default_sadikgroups(self, sadik):
        u'''
        Для ДОУ создаются возрастные группы, если они не существуют
        '''
        age_groups = sadik.age_groups.all()
        age_groups_created_ids = sadik.groups.active().values_list('age_group_id', flat=True)
        for age_group in age_groups:
            if age_group.id not in age_groups_created_ids:
                sadik_group = SadikGroup(sadik=sadik, age_group=age_group, year=get_current_distribution_year(),)
                sadik_group.min_birth_date = age_group.min_birth_date()
                sadik_group.max_birth_date = age_group.max_birth_date()
                sadik_group.save()

    def get_formset(self, sadik):
        return inlineformset_factory(Sadik, SadikGroup, form=get_sadik_group_form(sadik=sadik),
                                     formset=BaseSadikGroupFormSet,
                                     fields=('free_places',), extra=0, can_delete=False)

    def get(self, request, sadik):
        # создаем возрастные группы
        self.create_default_sadikgroups(sadik)
        formset = self.get_formset(sadik=sadik)(instance=sadik,
            queryset=SadikGroup.objects.active())
        return self.render_to_response(
            {'sadik': sadik, 'formset': formset})

    def post(self, request, sadik):
        formset = self.get_formset(sadik=sadik)(instance=sadik,
            queryset=SadikGroup.objects.active(),
            data=request.POST)
        if formset.is_valid():
            if any(form.has_changed() for form in formset.forms):
                for form in formset.forms:
                    if form.has_changed():
                        sadik_group = form.save()
                        Logger.objects.create_for_action(CHANGE_SADIK_GROUP_PLACES,
                            context_dict={'sadik_group': sadik_group},
                            extra={'user': request.user, 'obj': sadik_group, 'age_group': sadik_group.age_group})
                messages.success(request, u'Информация о группах %s изменена' % sadik)
            else:
                messages.success(request, u'Информация о группах %s осталась без изменений' % sadik)
            return HttpResponseRedirect(
                reverse('sadik_list_with_groups') + '#sadik_%d' % sadik.id)
        return self.render_to_response(
            {'sadik': sadik, 'formset': formset})


class RequestionListEnrollment(RequirePermissionsMixin, TemplateView):
    u"""список заявок, которым выделены места для выставления статуса зачисления"""
    template_name = "operator/requestion_list_distributed.html"
    required_permissions = ["is_operator", "is_sadik_operator"]

    def get(self, request, sadik_id):
#        получаем ДОУ для данного района в которых есть заявки с выделенными местами
        profile = request.user.get_profile()
        sadiks_query = Sadik.objects.filter(
            groups__vacancies__requestion__status__in=(
                STATUS_DECISION, STATUS_ABSENT, STATUS_NOT_APPEAR,
                STATUS_NOT_APPEAR_EXPIRE, STATUS_ABSENT_EXPIRE)).distinct(
                    ).filter_for_profile(profile).order_by('number')
        context = {
            'current_area': profile.area,
            'distribution_started': Distribution.objects.filter(
                status=DISTRIBUTION_STATUS_START).exists(),
        }
        if sadik_id:
            sadik = get_object_or_404(Sadik, id=sadik_id)
            form = SadikForm(sadiks_query=sadiks_query)
            context.update({
                'form': form,
            })
        elif sadiks_query.count() == 1:
            sadik = sadiks_query[0]
        else:
            form = SadikForm(sadiks_query=sadiks_query, data=request.GET)
            if form.is_valid():
                sadik = form.cleaned_data.get('sadik')
                if sadik:
                    return HttpResponseRedirect(reverse('requestion_list_enroll', kwargs={'sadik_id': sadik.id}))
            else:
                form = SadikForm(sadiks_query=sadiks_query)
                sadik = None
            context.update({
                'form': form,
            })
        if sadik:
            requestions_by_groups = []
            for sadik_group in sadik.groups.all():
                requestions_for_sadik = Requestion.objects.filter(
                    status__in=(STATUS_DECISION, STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE),
                    distributed_in_vacancy__sadik_group__sadik=sadik
                    ).select_related('distribute_in_group', 'profile'
                        ).order_by('-benefit_category__priority', 'registration_datetime', 'id')
                requestions_for_group = requestions_for_sadik.filter(
                    distributed_in_vacancy__sadik_group=sadik_group)
                if requestions_for_group:
                    requestions_by_groups.append(
                        (sadik_group, requestions_for_group))
            context.update({'sadik': sadik,
                            'appeal_statuses': [STATUS_ABSENT, STATUS_NOT_APPEAR],
                            'requestions_by_groups': requestions_by_groups,
                            "STATUS_NOT_APPEAR": STATUS_DISTRIBUTED,
                            "STATUS_REMOVE_REGISTRATION": STATUS_REMOVE_REGISTRATION,
                            "STATUS_REQUESTER": STATUS_REQUESTER})
            return self.render_to_response(context)
        return self.render_to_response(context)
