# -*- coding: utf-8 -*-
from datetime import timedelta
from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from sadiki.core.fields import TemplateFormField
from sadiki.core.models import Requestion, PROFILE_IDENTITY, Profile, \
    EvidienceDocument, REQUESTION_IDENTITY, AgeGroup, BenefitCategory, Area
from sadiki.core.utils import get_user_by_email, get_unique_username
from sadiki.core.widgets import JqueryUIDateWidget
import re


class PersonalDataApproveForm(forms.Form):
    approve_personal_data = forms.BooleanField(
        label=u"""Я согласен(а), что для получения электронной услуги мои 
            персональные данные будут обработаны в системе с соблюдением
            требований закона РФ от 27.07.2006 № 152-ФЗ \"О персональных данных\"""",
        help_text="Вам необходимо дать согласие для проведения регистрации",
        required=True)


class RegistrationForm(forms.ModelForm):
    u"""Форма регистрации для создания пользователя"""
    email = forms.EmailField(label=u'Электронная почта',
        help_text=u'''
        Электронная почта необходима для регистрации в электронной системе.
        Если у Вас нет адреса электронной почты, обратитесь к оператору РУО для очной регистрации
        ''')
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput,
        help_text=u'Введите пароль от учётной записи в "Электронной очереди"')
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        if get_user_by_email(self.cleaned_data.get('email', '')):
            raise forms.ValidationError(u'Такой адрес электронной почты уже зарегистрирован.')
        return self.cleaned_data['email']

    def clean_password1(self):
        if 'password1' in self.cleaned_data:
            password = self.cleaned_data['password1']
            # порверка что Email и пароль не совпадают
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
            raise forms.ValidationError(_("The two password fields didn't match."))
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
    template = TemplateFormField(destination=PROFILE_IDENTITY,
        label=u'Тип документа',
        help_text=u"Документ, удостоверяющий личность представителя ребенка")
    document_number = forms.CharField(label=u'Серия и номер документа',
        max_length=255)

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
#        проверяем, что номер документа соответствует шаблону
        if document_number and template and not re.match(
            template.regex, document_number):
            self._errors["document_number"] = self.error_class(
                [u'Не совпадает с шаблоном'])
            del cleaned_data['document_number']
            del cleaned_data['template']
        else:
            try:
                EvidienceDocument.objects.get(document_number=document_number,
                    confirmed=True, template=template)
            except EvidienceDocument.DoesNotExist:
                pass
            else:
                self._errors["document_number"] = self.error_class(
                    [u'Документ с таким номером уже занят'])
                del cleaned_data['document_number']
        return cleaned_data


class ProfileRegistrationForm(FormWithDocument):

    class Meta:
        model = Profile
        fields = ('last_name', 'first_name', 'patronymic',
            'phone_number', 'mobile_number')

    def __init__(self, *args, **kwds):
        super(ProfileRegistrationForm, self).__init__(*args, **kwds)
        self.fields['phone_number'].widget = forms.TextInput(attrs={'data-mask': '+7-999-99-99999'})
        self.fields['mobile_number'].widget = forms.TextInput(attrs={'data-mask': '+7-999-99-99999'})

    def clean(self, *args, **kwargs):
        cleaned_data = super(ProfileRegistrationForm, self).clean(
            *args, **kwargs)
        phone_number = cleaned_data.get('phone_number')
        mobile_number = cleaned_data.get('mobile_number')
        if not phone_number and not mobile_number:
            raise forms.ValidationError(u'Должен быть указан телефон для связи.')
        return cleaned_data

    def save(self, user, commit=True):
        profile = super(ProfileRegistrationForm, self).save(commit=False)
        profile.user = user
        if commit:
            profile.save()
            self.create_document(profile)
        return profile


class PublicSearchForm(forms.Form):
    birth_date = forms.DateField(label=u'Дата рождения ребёнка',
        widget=JqueryUIDateWidget(), required=True)
    registration_date = forms.DateField(label=u'Дата регистрации',
        widget=JqueryUIDateWidget(), required=False)
    number_in_old_list = forms.CharField(
        label=u'Номер в списке у заявок, поданных до запуска системы',
        required=False, widget=forms.TextInput())
    document_number = forms.CharField(label=u'Номер свидетельства о рождении',
        required=False, widget=forms.TextInput(attrs={'data-mask': '**-** 999999'}),
        help_text=u'Формат: II-ИВ 123456')
    parent_last_name = forms.CharField(label=u'Фамилия родителя',
        required=False, widget=forms.TextInput(), help_text=u'Только для заявок поданных до запуска системы')
    child_last_name = forms.CharField(label=u'Фамилия ребенка',
        required=False, widget=forms.TextInput(), help_text=u'Только для заявок поданных до запуска системы')

    field_map = {
        'birth_date': 'birth_date__exact',
        'registration_date': 'registration_datetime__range',
        'number_in_old_list': 'number_in_old_list__exact',
        'parent_last_name': 'profile__last_name__icontains',
        'child_last_name': 'last_name__icontains',
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
            if 'parent_last_name' in self.changed_data:
                filter_kwargs[self.field_map['parent_last_name']] = self.cleaned_data['parent_last_name']
            if 'child_last_name' in self.changed_data:
                filter_kwargs[self.field_map['child_last_name']] = self.cleaned_data['child_last_name']
            if 'document_number' in self.changed_data:
                requestion_ct = ContentType.objects.get_for_model(Requestion)
                requestion_ids = EvidienceDocument.objects.filter(content_type=requestion_ct,
                    confirmed=True, document_number=self.cleaned_data['document_number'],
                    template__destination=REQUESTION_IDENTITY).values_list('id', flat=True)
                filter_kwargs[self.field_map['document_number']] = requestion_ids
            return filter_kwargs


class QueueFilterForm(forms.Form):
    requestion_number = forms.CharField(label=u'Номер заявки в системе', required=False,
        widget=forms.TextInput(attrs={'data-mask': u'99999999999-Б-999999999'}),
        help_text=u"Укажите номер заявки к которой вы хотите перейти")
    confirmed = forms.BooleanField(label=u'Документально подтвержденные',
        required=False, help_text=u"Отметьте для исключения всех неподвержденных заявок из очереди")
    benefit_category = forms.ModelChoiceField(label=u'Категория льгот', required=False,
        queryset=BenefitCategory.objects.exclude_system_categories(),
        help_text=u"При выборе в очереди будут отображаться заявки только этой категории льгот")
    age_group = forms.ModelChoiceField(label=u'Возрастная категория',
        queryset=AgeGroup.objects.all(), required=False,
        help_text=u"При выборе в очереди будут отображаться заявки только этой возрастной категории")
    area = forms.ModelChoiceField(
        label=u'Территориальная области в которую заявка может быть зачислена',
        queryset=Area.objects.all(), empty_label=u"Весь муниципалитет",
        required=False, help_text=u"При выборе в очереди будут отображаться завки,\
            которые указали возможность зачисления в данную территориальную область"
    )

