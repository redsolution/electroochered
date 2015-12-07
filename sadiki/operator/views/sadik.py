# -*- coding: utf-8 -*-
import json

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse
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
            and request.user.profile.sadik_available(sadik))

    def dispatch(self, request, sadik_id):
        sadik = get_object_or_404(Sadik, id=sadik_id)
        return super(SadikOperatorSadikMixin, self).dispatch(request, sadik)


class SadikListWithGroups(SadikOperatorPermissionMixin, TemplateView):
    u"""для текущего распределения отображение списка ДОУ"""
    template_name = 'operator/sadik_list_with_groups.html'

    def get(self, request):
        distribution = Distribution.objects.active()
        context = {'distribution': distribution}
        profile = request.user.profile
#        получаем все ДОУ у которых есть возможность участвовать в распределении
        sadiks = Sadik.objects.filter_for_profile(profile)
        sadiks_dict = sadiks.add_related_groups()
        context.update({'sadiks': sadiks,
                        'area': profile.area})
        return self.render_to_response(context)


class SadikListWithGroupsJS(SadikOperatorPermissionMixin, TemplateView):
    u"""для текущего распределения отображение списка ДОУ"""
    template_name = 'operator/sadik_list_with_groups_js.html'

    def get_context_data(self, **kwargs):
        context = super(SadikListWithGroupsJS, self).get_context_data(**kwargs)
        distribution = Distribution.objects.active()
        context['distribution_is_active'] = json.dumps(bool(distribution))
        context['current_distribution_year'] = json.dumps(
            get_current_distribution_year().year)
        return context


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

    def get_formset(self, sadik):
        return inlineformset_factory(Sadik, SadikGroup, form=get_sadik_group_form(sadik=sadik),
                                     formset=BaseSadikGroupFormSet,
                                     fields=('free_places',), extra=0, can_delete=False)

    def get(self, request, sadik):
        # создаем возрастные группы
        sadik.create_default_sadikgroups()
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
    u"""список заявок, которым выделены места для выставления
    статуса зачисления
    """
    template_name = "operator/requestion_list_distributed.html"
    required_permissions = ["is_operator", "is_sadik_operator"]

    def get(self, request, sadik_id):
        # получаем ДОУ для данного района в которых есть заявки
        # с выделенными местами
        profile = request.user.profile
        sadiks_query = Sadik.objects.filter(
            groups__vacancies__requestion__status__in=(
                STATUS_DECISION, STATUS_ABSENT, STATUS_NOT_APPEAR,
                STATUS_NOT_APPEAR_EXPIRE, STATUS_ABSENT_EXPIRE)
        ).distinct().filter_for_profile(profile).order_by('number')
        context = {
            'current_area': profile.area,
            'distribution_started': Distribution.objects.filter(
                status=DISTRIBUTION_STATUS_START).exists(),
        }
        if sadik_id:
            sadik = get_object_or_404(Sadik, id=sadik_id)
            form = SadikForm(sadiks_query=sadiks_query)
            context.update({'form': form})
        elif sadiks_query.count() == 1:
            sadik = sadiks_query[0]
        else:
            form = SadikForm(sadiks_query=sadiks_query, data=request.GET)
            if form.is_valid():
                sadik = form.cleaned_data.get('sadik')
                if sadik:
                    return HttpResponseRedirect(reverse(
                        'requestion_list_enroll', kwargs={'sadik_id': sadik.id})
                    )
            else:
                form = SadikForm(sadiks_query=sadiks_query)
                sadik = None
            context.update({'form': form})
        if sadik:
            requestions_by_groups = []
            for sadik_group in sadik.groups.all():
                requestions_for_sadik = Requestion.objects.filter(
                    status__in=(STATUS_DECISION, STATUS_NOT_APPEAR,
                                STATUS_NOT_APPEAR_EXPIRE),
                    distributed_in_vacancy__sadik_group__sadik=sadik
                ).select_related('profile').order_by(
                    '-benefit_category__priority',
                    'registration_datetime', 'id')
                requestions_for_group = requestions_for_sadik.filter(
                    distributed_in_vacancy__sadik_group=sadik_group)
                if requestions_for_group:
                    requestions_by_groups.append(
                        (sadik_group, requestions_for_group))
            context.update({
                'sadik': sadik,
                'appeal_statuses': [STATUS_ABSENT, STATUS_NOT_APPEAR],
                'requestions_by_groups': requestions_by_groups,
                'STATUS_NOT_APPEAR': STATUS_DISTRIBUTED,
                'STATUS_REMOVE_REGISTRATION': STATUS_REMOVE_REGISTRATION,
                'STATUS_REQUESTER': STATUS_REQUESTER
            })
            return self.render_to_response(context)
        return self.render_to_response(context)


class DistributedRequestionsForSadik(RequirePermissionsMixin, TemplateView):
    required_permissions = ["is_operator", "is_sadik_operator"]

    def get(self, request, sadik_id):
        sadik = Sadik.objects.get(id=sadik_id)
        groups_with_distributed_requestions = sadik.get_groups_with_distributed_requestions()

        response = HttpResponse(content_type='application/vnd.ms-excel')
        file_name = u'Sadik_%s' % sadik.number
        response['Content-Disposition'] = u'attachment; filename="%s.xls"' % file_name
        import xlwt
        style = xlwt.XFStyle()
        style.num_format_str = 'DD-MM-YYYY'
        wb = xlwt.Workbook()
        ws = wb.add_sheet(u'Результаты распределения')
        header = [
            u'№',
            u'Номер заявки',
            u'Документ',
            u'Фамилия ребенка',
            u'Имя ребенка',
            u'Отчество ребенка',
            u'Дата рождения',
            u'Дата регистрации',
            u'Категория льгот',
            u'Статус заявки',
        ]
        ws.write_merge(0, 0, 0, len(header), sadik.name)
        row_number = 1
        for sadik_group, requestions in groups_with_distributed_requestions.iteritems():
            sadik_group_name = u"{name} ({short_name}) за {year} год".format(
                name=sadik_group.age_group.name, short_name=sadik_group.age_group.short_name,
                year=sadik_group.year.year)
            ws.write_merge(row_number, row_number, 0, len(header), sadik_group_name)
            row_number += 1
            for column_number, element in enumerate(header):
                ws.write(row_number, column_number, element, style)
            row_number += 1
            for i, requestion in enumerate(requestions, start=1):
                if requestion.related_documents:
                    document = requestion.related_documents[0]
                    document_number = u"{0} ({1})".format(
                        document.document_number, document.template.name)
                else:
                    document_number = u''
                row = [unicode(i), requestion.requestion_number,
                       document_number, requestion.child_last_name,
                       requestion.name, requestion.child_middle_name,
                       requestion.birth_date,
                       requestion.registration_datetime.date(),
                       unicode(requestion.benefit_category),
                       requestion.get_status_display()]
                for column_number, element in enumerate(row):
                    ws.write(row_number, column_number, element, style)
                row_number += 1
        wb.save(response)
        return response
