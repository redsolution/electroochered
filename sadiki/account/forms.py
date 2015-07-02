# -*- coding: utf-8 -*-
import datetime

from django import forms
from django.conf import settings
from django.forms.models import ModelForm
from django.forms.models import BaseModelFormSet
from django.forms.util import ErrorList
from django.contrib.auth.models import User
from sadiki.anonym.forms import FormWithDocument, TemplateFormField
from sadiki.core.fields import SadikWithAreasNameField
from sadiki.core.geo_field import location_errors
from sadiki.core.models import Profile, Requestion, Sadik, REQUESTION_IDENTITY,\
    Benefit, PersonalDocument, AGENT_TYPE_CHOICES
from sadiki.core.widgets import JqueryUIDateWidget, SelectMultipleJS, \
    JQueryUIAdmissionDateWidget, JqueryIssueDateWidget, SelectMultipleBenefits
from sadiki.core.widgets import ChoiceWithTextOptionWidget


class RequestionForm(FormWithDocument):
    template = TemplateFormField(
        destination=REQUESTION_IDENTITY, label=u'Тип документа')
    pref_sadiks = SadikWithAreasNameField(
        label=u'Выберите ДОУ', queryset=Sadik.objects.filter(
            active_registration=True).select_related('area'),
        required=True, widget=SelectMultipleJS(),
        help_text=u'Этот список не даёт прав на внеочередное зачисление '
                  u'в выбранные ДОУ')
    token = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Requestion
        _base_fields = ['areas', 'name', 'child_last_name', 'child_middle_name',
                        'token', 'birth_date', 'sex', 'template',
                        'birthplace', 'kinship', 'child_snils',
                        'document_number', 'district',
                        'pref_sadiks', 'location', 'admission_date']
        if settings.DESIRED_SADIKS == settings.DESIRED_SADIKS_CHOICE:
            _base_fields = _base_fields + ['distribute_in_any_sadik',]
        fields = _base_fields

    def __init__(self, *args, **kwds):
        self.base_fields['child_middle_name'].required = False
        self.base_fields['child_middle_name'].help_text = u'При наличии'
        self.base_fields['areas'].help_text = None
        self.base_fields['location'].label = u'Укажите ваше местоположение'
        self.base_fields['location'].required = True
        self.base_fields['location'].error_messages.update(location_errors)
        self.base_fields['template'].help_text = u"Документ, идентифицирующий\
            ребёнка"
        self.base_fields['birth_date'].widget = JqueryUIDateWidget()
        self.base_fields['admission_date'].widget = JQueryUIAdmissionDateWidget()
        self.base_fields['admission_date'].required = True
        self.base_fields['admission_date'].initial = datetime.date.today()
        self.base_fields['child_snils'].required = False
        default_snils_help_text = Requestion._meta.get_field(
            'child_snils').help_text
        self.base_fields['child_snils'].help_text = u'При наличии. {}'.format(
            default_snils_help_text)
        self.base_fields['kinship'].widget = ChoiceWithTextOptionWidget(
            choices=AGENT_TYPE_CHOICES)
        super(RequestionForm, self).__init__(*args, **kwds)

    def clean(self, *args, **kwargs):
        self.cleaned_data['distribute_in_any_sadik'] = True
        return super(RequestionForm, self).clean(*args, **kwargs)

    def save(self, profile, commit=True):
        requestion = super(RequestionForm, self).save(commit=False)
        requestion.profile = profile
        if commit:
            requestion.save()
            self.save_m2m()
            self.instance.document = self.create_document(requestion)

        return requestion


class ChangeRequestionForm(forms.ModelForm):

    class Meta:
        model = Requestion
        fields = ('name', 'sex', 'location', 'admission_date', 'district',
                  'child_middle_name', 'child_last_name',
                  'birthplace', 'kinship', 'child_snils',)

    def __init__(self, *args, **kwds):
        self.base_fields['child_middle_name'].required = False
        self.base_fields['child_middle_name'].help_text = u'При наличии'
        self.base_fields['location'].required = True
        self.base_fields['location'].label = u'Ваше местоположение'
        self.base_fields['location'].error_messages.update(location_errors)
        self.base_fields['admission_date'].widget = JQueryUIAdmissionDateWidget()
        self.base_fields['child_snils'].required = False
        default_snils_help_text = Requestion._meta.get_field(
            'child_snils').help_text
        self.base_fields['child_snils'].help_text = u'При наличии. {}'.format(
            default_snils_help_text)
        self.base_fields['kinship'].widget = ChoiceWithTextOptionWidget(
            choices=AGENT_TYPE_CHOICES)
        super(ChangeRequestionForm, self).__init__(*args, **kwds)


class BenefitsForm(forms.ModelForm):

    benefits = forms.ModelMultipleChoiceField(
        label=u'Льготы для заявки', 
        queryset=Benefit.objects,
        widget=SelectMultipleBenefits(), required=False,
        help_text=u'Выбранные льготы недействительны без документального '
                  u'подтверждения',
    )

    class Meta:
        model = Requestion
        fields = ('benefits',)


class PreferredSadikForm(forms.ModelForm):
    pref_sadiks = SadikWithAreasNameField(
        label=u'Выберите ДОУ', queryset=Sadik.objects.filter(
            active_registration=True).select_related('area'),
        required=False, widget=SelectMultipleJS())

    class Meta:
        model = Requestion
        fields = ('areas', 'pref_sadiks')


class SocialProfilePublicForm(ModelForm):
    class Meta:
        model = Profile
        fields = ('social_auth_public',)


class PersonalDataForm(ModelForm):
    first_name = forms.CharField(label=u'Имя', max_length=30, required=True)
    last_name = forms.CharField(label=u'Фамилия', max_length=30, required=True)

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'middle_name',
                  'phone_number', 'mobile_number',
                  'snils', 'town', 'street', 'house']

    def __init__(self, *args, **kwargs):
        self.base_fields['middle_name'].required = False
        self.base_fields['phone_number'].required = False
        self.base_fields['mobile_number'].required = False
        default_snils_help_text = Profile._meta.get_field('snils').help_text
        self.base_fields['snils'].help_text = u'При наличии. {}'.format(
            default_snils_help_text)
        self.base_fields['middle_name'].help_text = u'При наличии'
        self.base_fields['phone_number'].help_text = u'При наличии'
        self.base_fields['mobile_number'].help_text = u'При наличии'
        self.base_fields['snils'].required = False
        super(PersonalDataForm, self).__init__(*args, **kwargs)
        try:
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
        except:
            pass

    def save(self, commit=True):
        profile = super(PersonalDataForm, self).save(commit=False)
        profile.first_name = self.cleaned_data['first_name']
        profile.last_name = self.cleaned_data['last_name']
        profile.save()
        return profile


class PersonalDocumentForm(ModelForm):
    profile = forms.IntegerField(widget=forms.HiddenInput)
    doc_type = forms.ChoiceField(label=u'Тип документа',
                                 choices=PersonalDocument.DOC_TYPE_CHOICES)

    class Meta:
        model = PersonalDocument
        fields = ['doc_type', 'doc_name', 'profile', 'series',
                  'number', 'issued_date', 'issued_by']

    def clean_profile(self):
        return Profile.objects.get(id=self.cleaned_data['profile'])

    def __init__(self, *args, **kwargs):
        self.base_fields['issued_date'].widget = JqueryIssueDateWidget()
        super(PersonalDocumentForm, self).__init__(*args, **kwargs)


class BasePersonalDocumentFormset(BaseModelFormSet):

    def is_valid(self, *args, **kwargs):
        u""" возвращает True, если хотя бы одна форма валидна,
        и все валидные формы имеют различные типы документа.
        """
        all_valid_forms = [form for form in self.forms if form.is_valid()]
        if not all_valid_forms:
            return False
        used_doc_type_choices = set()
        validation_result = True
        for valid_form in all_valid_forms:
            doc_type_choice = int(valid_form.cleaned_data['doc_type'])
            if doc_type_choice in used_doc_type_choices:
                doc_type_errors = valid_form._errors.setdefault('doc_type',
                                                                ErrorList())
                doc_type_errors.append(u'Документ такого типа уже есть')
                validation_result = False
            used_doc_type_choices.add(doc_type_choice)
        return validation_result

    def has_changed(self, *args, **kwargs):
        for form in self.forms:
            if form.is_valid() and form.has_changed():
                return True
        return False

    def save(self, commit=True):
        for form in self.forms:
            if form.is_valid():
                form.save()


class EmailAddForm(forms.Form):
    email = forms.EmailField(label='Электронный почтовый адрес:')
