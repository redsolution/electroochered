# -*- coding: utf-8 -*-
import re
from datetime import timedelta

from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from sadiki.conf_settings import REQUESTION_NUMBER_MASK
from sadiki.core.fields import TemplateFormField, DateRangeField
from sadiki.core.models import Requestion, PROFILE_IDENTITY, Profile, \
    EvidienceDocument, REQUESTION_IDENTITY, AgeGroup, BenefitCategory, Area, \
    STATUS_CHOICES_FILTER, STATUS_KG_LEAVE
from sadiki.core.utils import get_unique_username, active_child_exist
from sadiki.core.widgets import JqueryUIDateWidget


# STATUS_CHOICES_EMPTY = (('', '---------'), ) + STATUS_CHOICES


class RegistrationForm(forms.ModelForm):
    u"""Форма регистрации для создания пользователя"""
    password1 = forms.CharField(
        label=_("Password"), widget=forms.PasswordInput(
            attrs={'placeholder':
                   u"Введите пароль для регистрации в электронной очереди"}))
    password2 = forms.CharField(
        label=_("Password confirmation"), widget=forms.PasswordInput(
            attrs={'placeholder':
                   u"Введите тот же пароль, что и выше, для подтверждения"}))

    class Meta:
        model = User
        fields = ('password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

    def clean_password1(self):
        if 'password1' in self.cleaned_data:
            password = self.cleaned_data['password1']
            # проверка, что Email и пароль не совпадают
            if 'username' in self.cleaned_data:
                if password == self.cleaned_data['username']:
                    raise forms.ValidationError(
                        u'Пароль не может совпадать с адресом электронной почты')
            # проверка длины пароля
            if len(password) <= 4:
                raise forms.ValidationError(u'Слишком короткий пароль')

        return self.cleaned_data['password1']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(u"Введенные пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.username = get_unique_username()
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class FormWithDocument(forms.ModelForm):
    template = TemplateFormField(
        destination=PROFILE_IDENTITY, label=u'Тип документа',
        help_text=u"Документ, удостоверяющий личность представителя ребенка")
    document_number = forms.CharField(
        label=u'Серия и номер документа', max_length=255,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def create_document(self, requestion, commit=True):
        document = EvidienceDocument(
            template=self.cleaned_data.get('template'),
            document_number=self.cleaned_data.get('document_number'),
            object_id=self.instance.id,
            content_type=ContentType.objects.get_for_model(self.instance)
            )
        if commit:
            document.save()
        return document

    def clean(self):
        cleaned_data = self.cleaned_data
        document_number = self.cleaned_data.get('document_number')
        template = self.cleaned_data.get('template')
        # проверяем, что номер документа соответствует шаблону
        if document_number and template and not re.match(
            template.regex, document_number):
            self._errors["document_number"] = self.error_class([u'Неверный формат'])
            del cleaned_data['document_number']
            del cleaned_data['template']
        # проверяем на наличие подтвержденных заявок с таким же документом
        else:
            documents = EvidienceDocument.objects.filter(
                document_number=document_number, confirmed=True,
                template=template)
            if documents:
                requestions_ids = documents.values_list('object_id', flat=True)
                # заявки в статусе "Выпущен из ДОУ" могут содержать
                # повторяющиеся номера документов
                requestions = Requestion.objects.filter(
                    id__in=requestions_ids).exclude(status=STATUS_KG_LEAVE)
                if requestions.exists():
                    self._errors["document_number"] = self.error_class(
                        [u"Документ с таким номером уже занят"])
                    del cleaned_data['document_number']
                    # возвращаем значение, чтобы не выполнять ненужных проверок
                    # на наличие ребенка в ЭС
                    return cleaned_data
            # проверяем по номеру документа наличие и статус ребенка в ЭС
            if active_child_exist(document_number):
                self._errors["document_number"] = self.error_class(
                    [u"Ребенок с таким документом уже посещает ДОУ"])
                del cleaned_data['document_number']
        return cleaned_data


class PublicSearchForm(forms.Form):
    birth_date = forms.DateField(
        label=u'Дата рождения ребёнка',
        widget=JqueryUIDateWidget(), required=True)
    registration_date = forms.DateField(
        label=u'Дата регистрации', widget=JqueryUIDateWidget(), required=False)
    number_in_old_list = forms.CharField(
        label=u'Номер в списке у заявок, поданных до запуска системы',
        required=False, widget=forms.TextInput())
    document_number = forms.CharField(
        label=u'Номер свидетельства о рождении', required=False,
        widget=forms.TextInput(), help_text=u'Формат: II-ИВ 123456')
    child_name = forms.CharField(
        label=u'Имя ребёнка', required=False, widget=forms.TextInput(),
        help_text=u'Только для заявок, поданных до запуска системы')

    field_map = {
        'birth_date': 'birth_date__exact',
        'registration_date': 'registration_datetime__range',
        'number_in_old_list': 'number_in_old_list__exact',
        'child_name': 'name__icontains',
        'document_number': 'id__in'
    }

    def __init__(self, *args, **kwds):
        super(PublicSearchForm, self).__init__(*args, **kwds)
        self.reverse_field_map = dict((v, k) for k, v in self.field_map.iteritems())

    def build_query(self):
        if self.cleaned_data:
            filter_kwargs = {}
            if 'birth_date' in self.changed_data:
                filter_kwargs[self.field_map['birth_date']] = self.cleaned_data['birth_date']
            if 'registration_date' in self.changed_data:
                filter_kwargs[self.field_map['registration_date']] = (
                    self.cleaned_data['registration_date'],
                    self.cleaned_data['registration_date'] + timedelta(days=1),
                )
            if 'number_in_old_list' in self.changed_data:
                filter_kwargs[self.field_map['number_in_old_list']] = self.cleaned_data['number_in_old_list']
            if 'child_name' in self.changed_data:
                filter_kwargs[self.field_map['child_name']] = self.cleaned_data['child_name']
            if 'document_number' in self.changed_data:
                requestion_ct = ContentType.objects.get_for_model(Requestion)
                requestion_ids = EvidienceDocument.objects.filter(
                    content_type=requestion_ct,
                    document_number=self.cleaned_data['document_number'],
                    template__destination=REQUESTION_IDENTITY
                ).values_list('object_id', flat=True)
                filter_kwargs[self.field_map['document_number']] = requestion_ids
            return filter_kwargs


class QueueFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(QueueFilterForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'requestion_number',
            'status',
            'area',
            'age_group',
            'benefit_category',
            'admission_date',
            'decision_date',
            'without_facilities',
        ]
        admission_date_choices = [
            (year.year, year.year) for year in
            Requestion.objects.queue().dates('admission_date', 'year')]
        admission_date_choices = [('', '---------'),] + admission_date_choices
        self.fields['admission_date'].choices = admission_date_choices
        decision_date_choices = [
            (year.year,year.year) for year in
            Requestion.objects.queue().dates('decision_datetime', 'year')]
        decision_date_choices = [('', '---------'),] + decision_date_choices
        self.fields['decision_date'].choices = decision_date_choices
        
    requestion_number = forms.CharField(
        label=u'Номер заявки в системе', required=False,
        widget=forms.TextInput(attrs={'data-mask': REQUESTION_NUMBER_MASK}),
        help_text=u"Укажите номер заявки, к которой вы хотите перейти")
    not_appeared = forms.BooleanField(
        label=u'Показать только неявившиеся заявки', required=False,
        help_text=u"Отметьте для отображения неявившихся заявок из очереди")
    status = forms.MultipleChoiceField(
        label=u'Статус заявки', required=False, choices=STATUS_CHOICES_FILTER,
        help_text=u"При выборе в очереди будут отображаться заявки "
                  u"только с выбранным статусом")
    benefit_category = forms.ModelChoiceField(
        label=u'Категория льгот', required=False,
        queryset=BenefitCategory.objects.exclude_system_categories(),
        help_text=u"При выборе в очереди будут отображаться заявки "
                  u"только этой категории льгот")
    age_group = forms.ModelChoiceField(
        label=u'Возрастная категория',
        queryset=AgeGroup.objects.all(), required=False,
        help_text=u"При выборе в очереди будут отображаться заявки "
                  u"только этой возрастной категории")
    area = forms.ModelMultipleChoiceField(
        label=u'Группа ДОУ для зачисления', queryset=Area.objects.all(),
        required=False,
        help_text=u"При выборе в очереди будут отображаться заявки, "
                  u"для которых указана возможность зачисления в эту группу ДОУ"
    )
    admission_date = forms.ChoiceField(
        label=u'Желаемый год зачисления', required=False,
        help_text=u"При выборе в очереди будут отображаться заявки "
                  u"только с указанным годом зачисления"
    )
    decision_date = forms.ChoiceField(
        label=u'Фактический год зачисления', required=False,
        help_text=u"При выборе в очереди будут отображаться заявки "
                  u"только с указанным фактическим годом зачисления "
    )
    without_facilities = forms.BooleanField(
        label=u"Сортировать очередь", required=False,
        widget=forms.Select(choices=((False, u'в порядке очерёдности'),
                                     (True, u'в порядке подачи заявлений'))),
        help_text=mark_safe(
            u"""В порядке очередности заявки отображаются исходя из приоритета
            категории льгот:
            внеочередная, первоочередная, заявки без льгот.<br>
            В порядке подачи заявлений заявки отображаются только
            хронологически."""))
