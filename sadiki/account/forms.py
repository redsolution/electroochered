# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.gis.forms.fields import GeometryField
from django.forms.models import BaseInlineFormSet, ModelForm
from sadiki.anonym.forms import FormWithDocument, TemplateFormField
from sadiki.core.fields import SadikWithAreasNameField
from sadiki.core.geo_field import map_widget, location_errors
from sadiki.core.models import EvidienceDocumentTemplate, \
    Profile, Requestion, Sadik, BENEFIT_DOCUMENT, REQUESTION_IDENTITY, Benefit, \
    BenefitCategory, Address
from sadiki.core.settings import BENEFIT_SYSTEM_MIN
from sadiki.core.widgets import JqueryUIDateWidget, SelectMultipleJS


class RequestionPrefSadiksMixin(object):
    u"""проверяем, что выбранные ДОУ из той области, куда хочет быть зачислен пользователь"""

    def clean(self, *args, **kwargs):
        pref_sadiks = self.cleaned_data.get("pref_sadiks")
        distribute_in_any_sadik = self.cleaned_data.get('distribute_in_any_sadik')
        if not distribute_in_any_sadik and not pref_sadiks:
            raise forms.ValidationError(u'Необходимо указать приоритетные ДОУ или возможность зачисления в любой ДОУ')
        return super(RequestionPrefSadiksMixin, self).clean(*args, **kwargs)


class RequestionForm(RequestionPrefSadiksMixin, FormWithDocument):
    name = forms.CharField(label=u"Имя ребёнка", max_length=20,
                           help_text=u"В поле достаточно ввести только имя ребёнка. Фамилию и отчество вводить не нужно!")
    template = TemplateFormField(destination=REQUESTION_IDENTITY,
        label=u'Тип документа')
    pref_sadiks = SadikWithAreasNameField(
        label=u'Выберите ДОУ', queryset=Sadik.objects.filter(active_registration=True).select_related('area'),
        required=False, widget=SelectMultipleJS(),
        help_text=u'Этот список не даёт прав на внеочередное зачисление в выбранные ДОУ')

    class Meta:
        model = Requestion
        _base_fields = ['areas', 'name',
                        'birth_date', 'sex', 'template',
                        'document_number',
                        'pref_sadiks', 'location']
        if settings.DESIRED_DATE != settings.DESIRED_DATE_NO:
            _base_fields += ['admission_date',]
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
        super(RequestionForm, self).__init__(*args, **kwds)

    def save(self, profile, commit=True):
        requestion = super(RequestionForm, self).save(commit=False)
        requestion.profile = profile
        if commit:
            requestion.save()
            self.save_m2m()
            self.create_document(requestion)

        return requestion


class ChangeRequestionBaseForm(forms.ModelForm):
    name = forms.CharField(
        label=u"Имя ребёнка", max_length=20,
        help_text=u"В поле достаточно ввести только имя ребёнка. Фамилию и отчество вводить не нужно!")

    class Meta:
        model = Requestion
        _base_fields = ('name', 'sex', 'location')
        if settings.DESIRED_DATE == settings.DESIRED_DATE_NO:
            fields = _base_fields
        else:
            fields = _base_fields + ('admission_date',)


class ChangeRequestionForm(ChangeRequestionBaseForm):

    def __init__(self, *args, **kwds):
        self.base_fields['location'].widget = map_widget()
        self.base_fields['location'].required = True
        self.base_fields['location'].error_messages.update(location_errors)
        super(ChangeRequestionForm, self).__init__(*args, **kwds)


class BenefitsForm(forms.ModelForm):

    benefits = forms.ModelMultipleChoiceField(label=u'Льготы для заявки',
        queryset=Benefit.objects.all(), widget=SelectMultipleJS(),
        help_text=u'Выбранные льготы недействительны без документального подтверждения',
        required=False
    )

    class Meta:
        model = Requestion
        fields = ('benefits',)


class BenefitCategoryForm(forms.ModelForm):
    class Meta:
        model = Requestion
        fields = ('benefit_category',)

    def __init__(self, *args, **kwargs):
#        убираем из категорий льгот системные
        self.base_fields['benefit_category'].queryset = BenefitCategory.objects.filter(
            priority__lt=BENEFIT_SYSTEM_MIN)
        super(BenefitCategoryForm, self).__init__(*args, **kwargs)
        self.fields['benefit_category'].empty_label = None


class BaseRequestionsFormSet(BaseInlineFormSet):

    def clean(self, *args, **kwargs):
        super(BaseRequestionsFormSet, self).clean(*args, **kwargs)
        if any(self.errors):
#         Don't bother validating the formset unless each form is valid on its own
            return
        sadiks = []
        for form_data in self.cleaned_data:
            sadik = form_data.get('sadik', None)
            if sadik:
                if sadik in sadiks:
                    raise forms.ValidationError(u'Не должно быть совпадающих ДОУ.')
                else:
                    sadiks.append(sadik)


class PreferredSadikForm(RequestionPrefSadiksMixin, forms.ModelForm):
    pref_sadiks = forms.ModelMultipleChoiceField(label=u'Выберите ДОУ',
        queryset=Sadik.objects.filter(active_registration=True),
        required=False, widget=SelectMultipleJS())

    class Meta:
        model = Requestion
        _base_fields = ('areas', 'pref_sadiks',)
        if settings.DESIRED_SADIKS == settings.DESIRED_SADIKS_CHOICE:
            _base_fields = _base_fields + ('distribute_in_any_sadik',)
        fields = _base_fields


class PreferredSadikWithAreasNameForm(PreferredSadikForm):
    pref_sadiks = SadikWithAreasNameField(
        label=u'Выберите ДОУ', queryset=Sadik.objects.filter(active_registration=True).select_related('area'),
        required=False, widget=SelectMultipleJS())


class DocumentForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.fields['template'].queryset = EvidienceDocumentTemplate.objects.filter(
            destination=BENEFIT_DOCUMENT)


class SocialProfilePublicForm(ModelForm):
    class Meta:
        model = Profile
        fields = ('social_auth_public',)