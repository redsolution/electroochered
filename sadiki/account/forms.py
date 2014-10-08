# -*- coding: utf-8 -*-
import datetime

from django import forms
from django.conf import settings
from django.forms.models import ModelForm
from sadiki.anonym.forms import FormWithDocument, TemplateFormField
from sadiki.core.fields import SadikWithAreasNameField
from sadiki.core.geo_field import location_errors
from sadiki.core.models import Profile, Requestion, Sadik, REQUESTION_IDENTITY,\
    Benefit
from sadiki.core.widgets import JqueryUIDateWidget, SelectMultipleJS, \
    JQueryUIAdmissionDateWidget


class RequestionForm(FormWithDocument):
    name = forms.CharField(
        label=u"Имя ребёнка", max_length=20,
        help_text=u"В поле достаточно ввести только имя ребёнка. "
                  u"Фамилию и отчество вводить не нужно!")
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
        _base_fields = ['areas', 'name', 'token',
                        'birth_date', 'sex', 'template',
                        'document_number', 'district',
                        'pref_sadiks', 'location', 'admission_date']
        if settings.DESIRED_SADIKS == settings.DESIRED_SADIKS_CHOICE:
            _base_fields = _base_fields + ['distribute_in_any_sadik',]
        fields = _base_fields

    def __init__(self, *args, **kwds):
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
    name = forms.CharField(
        label=u"Имя ребёнка", max_length=20,
        help_text=u"В поле достаточно ввести только имя ребёнка. "
                  u"Фамилию и отчество вводить не нужно!")

    class Meta:
        model = Requestion
        fields = ('name', 'sex', 'location', 'admission_date', 'district')

    def __init__(self, *args, **kwds):
        self.base_fields['location'].required = True
        self.base_fields['location'].label = u'Ваше местоположение'
        self.base_fields['location'].error_messages.update(location_errors)
        self.base_fields['admission_date'].widget = JQueryUIAdmissionDateWidget()
        super(ChangeRequestionForm, self).__init__(*args, **kwds)


class BenefitsForm(forms.ModelForm):

    benefits = forms.ModelMultipleChoiceField(
        label=u'Льготы для заявки', 
        queryset=Benefit.objects,
        widget=SelectMultipleJS(), required=False,
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


class EmailAddForm(forms.Form):
    email = forms.EmailField(label='Электронный почтовый адрес:')