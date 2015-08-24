# -*- coding: utf-8 -*-
import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.generic import BaseGenericInlineFormSet
from django.forms.formsets import DELETION_FIELD_NAME
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import CheckboxSelectMultiple
from sadiki.account.forms import RequestionForm, ChangeRequestionForm
from sadiki.account.forms import PreferredSadikForm
from sadiki.administrator.admin import SadikAdminForm
from sadiki.anonym.forms import PublicSearchForm, FormWithDocument, QueueFilterForm
from sadiki.conf_settings import REQUESTION_NUMBER_MASK
from sadiki.core.fields import TemplateFormField, DateRangeField
from sadiki.core.models import SadikGroup, AgeGroup, Vacancies, \
    VACANCY_STATUS_PROVIDED, REQUESTION_IDENTITY, Sadik, \
    STATUS_REQUESTER, REQUESTION_TYPE_OPERATOR, Requestion, EvidienceDocument, EvidienceDocumentTemplate, BENEFIT_DOCUMENT, NOT_CONFIRMED_STATUSES
from sadiki.core.utils import get_current_distribution_year, get_user_by_email
from sadiki.core.widgets import JqueryUIDateWidget, LeafletMap
from sadiki.core.utils import reorder_fields


def select_list_from_qs(queryset, requestion):
    u"""Делает из queryset список для параметра choices"""
    select_list = []
    for obj in queryset:
        groups = requestion.get_sadik_groups(obj)
        select_list.append((obj.id, u'%d мест %s' % (groups[0].free_places, unicode(obj))))
    return select_list


class QueueOperatorFilterForm(QueueFilterForm):
    def __init__(self, *args, **kwargs):
        super(QueueOperatorFilterForm, self).__init__(*args, **kwargs)
        fields_order = [
            'requestion_number',
            'status',
            'area',
            'benefit_category',
            'age_group',        
            'birth_date',
            'admission_date',
            'decision_date',
            'without_facilities',
        ]
        self.fields = reorder_fields(self.fields, fields_order)
        admission_date_choices = [
            (year, year.year) for year in
            Requestion.objects.queue().dates('admission_date', 'year')]
        admission_date_choices = [('', '---------'),] + admission_date_choices
        self.fields['admission_date'].choices = admission_date_choices
        decision_date_choices = [
            (year.year,year.year) for year in
            Requestion.objects.queue().dates('decision_datetime', 'year')]
        decision_date_choices = [('', '---------'),] + decision_date_choices
        self.fields['decision_date'].choices = decision_date_choices

    birth_date = DateRangeField(
        label=u"Дата рождения", required=False,
        help_text=u"При выборе в очереди будут отображаться заявки, относящиеся"
                  u" к указанному диапазону дат рождения от/до (включительно)")


class OperatorRequestionForm(RequestionForm):
    u"""Форма регистрации заявки через оператора"""

    def __init__(self, *args, **kwargs):
        super(OperatorRequestionForm, self).__init__(*args, **kwargs)
        self.fields['location'].label = u'Укажите местоположение заявителя'
        self.fields['areas'].label = u'Выберите группы ДОУ'
        self.fields['pref_sadiks'].label = u'Выберите ДОУ'
        self.fields['location'].help_text = ''
        self.fields['areas'].help_text = ''
        self.fields['pref_sadiks'].help_text = ''

    def create_document(self, requestion, commit=True):
        document = super(OperatorRequestionForm, self).create_document(
            requestion, commit=False)
#        документ документально подтвержден, т.к. добавлен оператором
        document.confirmed = True
        if commit:
            document.save()
        return document
    
    def save(self, *args, **kwargs):
        self.instance.status = STATUS_REQUESTER
        self.instance.cast = REQUESTION_TYPE_OPERATOR
        return super(OperatorRequestionForm, self).save(*args, **kwargs)


class OperatorChangeRequestionForm(ChangeRequestionForm):

    def __init__(self, *args, **kwargs):
        super(OperatorChangeRequestionForm, self).__init__(*args, **kwargs)
        self.fields['location'].label = u"Местоположение заявителя"
        self.fields['location'].help_text = ''


class OperatorPreferredSadikForm(PreferredSadikForm):

    def __init__(self, *args, **kwargs):
        super(OperatorPreferredSadikForm, self).__init__(*args, **kwargs)
        self.fields['areas'].help_text = ''
        self.fields['pref_sadiks'].help_text = ''


class OperatorSearchForm(PublicSearchForm):
    requestion_number = forms.CharField(label=u'Номер заявки в системе',
        required=False, widget=forms.TextInput(attrs={'data-mask': REQUESTION_NUMBER_MASK}))
    birth_date = forms.DateField(label=u'Дата рождения ребёнка',
            widget=JqueryUIDateWidget(), required=False)

    field_map = {
        'requestion_number': 'requestion_number__exact',
        'birth_date': 'birth_date__exact',
        'registration_date': 'registration_datetime__range',
        'number_in_old_list': 'number_in_old_list__exact',
        'child_name': 'name__icontains',
        'document_number': 'id__in'
    }

    def build_query(self):
        if self.cleaned_data:
            filter_kwargs = PublicSearchForm.build_query(self)
            if filter_kwargs is None:
                filter_kwargs = {}
            if 'requestion_number' in self.changed_data:
                filter_kwargs[self.field_map['requestion_number']] = self.cleaned_data['requestion_number']
            return filter_kwargs

    def clean(self):
        if not [value for key, value in self.cleaned_data.iteritems() if value]:
            raise forms.ValidationError(u"Необходимо указать параметры для поиска")
        else:
            return self.cleaned_data

def get_sadik_group_form(sadik):
    class SadikGroupForm(forms.ModelForm):

        age_group = forms.ModelChoiceField(queryset=AgeGroup.objects.exclude(
                    id__in=sadik.groups.active().values_list('age_group__id', flat=True)),
            label=u'Возрастная категория')

        def __init__(self, *args, **kwds):
            super(SadikGroupForm, self).__init__(*args, **kwds)
            # Для новых групп исключить изменение возрастной категории
            if self.instance.pk:
                del self.fields['age_group']

        class Meta:
            model = SadikGroup
            fields = '__all__'

        def save(self, commit=True):
            free_places = self.cleaned_data.get('free_places')
            self.instance.capacity = free_places
            if not self.initial:
                # Создание новой группы
                self.instance.year = get_current_distribution_year()
                self.instance.min_birth_date = self.cleaned_data['age_group'].min_birth_date()
                self.instance.max_birth_date = self.cleaned_data['age_group'].max_birth_date()
            return super(SadikGroupForm, self).save(commit)
    return SadikGroupForm


class BaseSadikGroupFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        age_groups = []
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            age_group = form.cleaned_data.get('age_group')
            if age_group:
                if age_group in age_groups:
                    raise forms.ValidationError(u"В ДОУ не может быть двух одинаковых возрастных групп")
                age_groups.append(age_group)


class SadikForm(forms.Form):

    def __init__(self, sadiks_query, *args, **kwargs):
        super(SadikForm, self).__init__(*args, **kwargs)
        self.fields['sadik'] = forms.ModelChoiceField(queryset=sadiks_query,
            label=u'Выберите ДОУ', required=False)


class RequestionIdentityDocumentForm(FormWithDocument):
    template = TemplateFormField(destination=REQUESTION_IDENTITY,
        label=u'Тип документа')

    def create_document(self, requestion, commit=True):
        document = super(RequestionIdentityDocumentForm, self).create_document(
            requestion, commit=False)
        # в зависимости от статуса заявки(документ может быть задан для снятой с учета заявки)
        # документ может быть подтвержден или нет
        if requestion.status not in NOT_CONFIRMED_STATUSES:
            document.confirmed = True
        if commit:
            document.save()
        return document

    def save(self, commit=True):
        requestion = super(RequestionIdentityDocumentForm, self).save(commit)
        if commit:
            self.create_document(requestion)
        return requestion


class ChangeSadikForm(SadikAdminForm):
    class Meta(SadikAdminForm.Meta):
        fields = ('postindex', 'street', 'building_number', 'email', 'site',
            'head_name', 'phone', 'cast', 'tech_level', 'training_program',
            'route_info', 'extended_info', 'active_registration',
            'active_distribution', 'age_groups',)
        
    def __init__(self, *args, **kwargs):
        super(ChangeSadikForm, self).__init__(*args, **kwargs)
        self.fields["coords"].widget = LeafletMap()

    def save(self, commit=True):
        """
        Given a model instance save it to the database.
        """
        sadik = super(ChangeSadikForm, self).save(commit)

        if commit:
            address, created = self.get_address()
            sadik.address = address
            sadik.save()
        return sadik


class BaseConfirmationFormMixin(object):

    def __init__(self, *args, **kwargs):
        self.base_fields['reason'] = forms.CharField(label=u"Основание",
            help_text=u"Внимание! Эта информация будет публично доступной, старайтесь не указывать персональные данные",
            widget=forms.Textarea(attrs={'rows': 2, 'cols': 12}))
        super(BaseConfirmationFormMixin, self).__init__(*args, **kwargs)


class BaseConfirmationForm(BaseConfirmationFormMixin, forms.Form):
    pass


class ConfirmationFormMixin(BaseConfirmationFormMixin):

    def __init__(self, *args, **kwargs):
        self.base_fields['confirm'] = forms.BooleanField(initial=True, widget=forms.HiddenInput())
        self.base_fields['transition'] = forms.IntegerField(widget=forms.HiddenInput())
        super(ConfirmationFormMixin, self).__init__(*args, **kwargs)


class ConfirmationForm(ConfirmationFormMixin, forms.Form):

    def __init__(self, requestion, *args, **kwds):
        self.requestion = requestion
        super(ConfirmationForm, self).__init__(*args, **kwds)


class TempDistributionConfirmationForm(ConfirmationForm):
    sadik = forms.ModelChoiceField(queryset=Sadik.objects.all(), label="Выберите ДОУ")

    def __init__(self, *args, **kwds):
        super(TempDistributionConfirmationForm, self).__init__(*args, **kwds)
        vacancies_query = self.requestion.available_temp_vacancies()
        sadik_query = Sadik.objects.filter(id__in=vacancies_query.values_list('sadik_group__sadik__id'))
        self.fields['sadik'].queryset = sadik_query


class ImmediatelyDistributionConfirmationForm(ConfirmationForm):
    sadik = forms.ModelChoiceField(queryset=Sadik.objects.all(), label="Выберите ДОУ")

    def __init__(self, *args, **kwds):
        super(ImmediatelyDistributionConfirmationForm, self).__init__(*args, **kwds)
        available_sadiks_ids = self.requestion.get_sadiks_groups(
            ).values_list('sadik', flat=True)
        preferred_sadiks = self.requestion.pref_sadiks.filter(
            id__in=available_sadiks_ids)
        any_sadiks = Sadik.objects.exclude(id__in=preferred_sadiks).filter(
            id__in=available_sadiks_ids)

        choices = []
        if preferred_sadiks:
            choices.append((u'Предпочитаемые ДОУ', select_list_from_qs(preferred_sadiks, self.requestion)))
        else:
            choices.append((u'ДОУ этой территориальной области', select_list_from_qs(any_sadiks, self.requestion)))

        self.fields['sadik'].queryset = Sadik.objects.filter(id__in=available_sadiks_ids)
        self.fields['sadik'].choices = choices


class ProfileSearchForm(forms.Form):
    username = forms.CharField(label=u"Имя пользователя, подавшего заявку", required=False,
                               help_text=u'Имя, используемое пользователем для входа в систему')
    requestion_number = forms.CharField(
        label=u'Номер заявки, привязанной к профилю',
        required=False,
        widget=forms.TextInput(attrs={'data-mask': REQUESTION_NUMBER_MASK}))
    parent_first_name = forms.CharField(
        label=u'Имя родителя', required=False, widget=forms.TextInput())

    field_map = {
        'username': 'user__username__exact',
        'requestion_number': 'requestion__requestion_number__exact',
        'parent_first_name': 'user__first_name__icontains',
    }

    def __init__(self, *args, **kwds):
        super(ProfileSearchForm, self).__init__(*args, **kwds)
        self.reverse_field_map = dict((v, k) for k, v in self.field_map.iteritems())

    def clean(self):
        if not any([value for value in self.cleaned_data.itervalues()]):
            raise forms.ValidationError(u"Необходимо указать хотя бы один параметр для поиска.")
        return self.cleaned_data

    def build_query(self):
        if self.cleaned_data:
            filter_kwargs = {}
            requestion_number = self.cleaned_data.get('requestion_number')
            parent_first_name = self.cleaned_data.get('parent_first_name')
            username = self.cleaned_data.get('username')
            if username:
                filter_kwargs[self.field_map['username']] = username
            if requestion_number:
                filter_kwargs[self.field_map['requestion_number']] = requestion_number
            if parent_first_name:
                filter_kwargs[self.field_map['parent_first_name']] = parent_first_name
            return filter_kwargs


class HiddenConfirmation(forms.Form):
    action = forms.CharField(widget=forms.HiddenInput)


class ChangeLocationForm(forms.ModelForm):

    class Meta:
        model = Requestion
        fields = ('location',)

    def __init__(self, *args, **kwargs):

        super(ChangeLocationForm, self).__init__(*args, **kwargs)
        self.fields['location'].widget = forms.HiddenInput()


class RequestionConfirmationForm(forms.Form):
    name_confirm = forms.BooleanField()
    birth_date_confirm = forms.BooleanField()
    document_confirm = forms.BooleanField()
    benefits_confirm = forms.BooleanField()

    def __init__(self, requestion, *args, **kwargs):
        super(RequestionConfirmationForm, self).__init__(*args, **kwargs)

    def clean(self):
        if not all(self.cleaned_data.values()):
            raise forms.ValidationError(u"Необходимо подтвердить все данные заявки.")
        return self.cleaned_data


class CustomGenericInlineFormSet(BaseGenericInlineFormSet):

    def add_fields(self, form, index):
        super(CustomGenericInlineFormSet, self).add_fields(form, index)
        form.fields[DELETION_FIELD_NAME].widget.attrs = {'class': 'delete'}

    def save(self, commit=True):
        instances = super(CustomGenericInlineFormSet, self).save(commit=False)
        for instance in instances:
            # Do something with `instance`
            instance.confirmed = True
            if commit:
                instance.save()
        if commit:
            self.save_m2m()
        return instances


class DocumentForm(forms.ModelForm):

    class Meta:
        model = EvidienceDocument
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.fields['template'].widget = forms.HiddenInput()
        self.fields['template'].queryset = EvidienceDocumentTemplate.objects.filter(
            destination=BENEFIT_DOCUMENT)

    def clean(self):
        cleaned_data = self.cleaned_data
        document_number = self.cleaned_data.get('document_number')
        template = self.cleaned_data.get('template')
#        проверяем, что номер документа соответствует шаблону
        if document_number and template and not re.match(
            template.regex, document_number):
            self._errors["document_number"] = self.error_class(
                [u'Неверный формат'])
        return cleaned_data
