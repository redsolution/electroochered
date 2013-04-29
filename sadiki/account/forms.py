# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.contrib import admin
from django.forms.models import BaseInlineFormSet, ModelForm
from sadiki.anonym.forms import FormWithDocument, TemplateFormField
from sadiki.core.models import EvidienceDocumentTemplate, \
    Profile, Requestion, Sadik, BENEFIT_DOCUMENT, REQUESTION_IDENTITY, Benefit, \
    BenefitCategory, Address
from sadiki.core.settings import BENEFIT_SYSTEM_MIN
from sadiki.core.widgets import JqueryUIDateWidget, SelectMultipleJS, PrefSadiksJS


class RequestionPrefSadiksMixin(object):
    u"""проверяем, что выбранные ДОУ из той области, куда хочет быть зачислен пользователь"""

    def clean(self, *args, **kwargs):
        areas = self.cleaned_data.get('areas')
        pref_sadiks = self.cleaned_data.get("pref_sadiks")
        areas = self.cleaned_data.get('areas')
        if areas and pref_sadiks:
            pref_sadiks_areas_set = set(pref_sadiks.values_list('area', flat=True))
            requestion_areas_set = set([area.id for area in areas])
            if not pref_sadiks_areas_set.issubset(requestion_areas_set):
                raise forms.ValidationError(u"""Выбранные приоритетные ДОУ должны принадлежать
                    к выбранным территориальным областям""")
        elif not areas and not pref_sadiks:
            raise forms.ValidationError(
                u"""Если для зачисления указан весь муниципалитет, то
                необходимо указать приоритетные ДОУ.""")
        distribute_in_any_sadik = self.cleaned_data.get('distribute_in_any_sadik')
        if not distribute_in_any_sadik and not pref_sadiks:
            raise forms.ValidationError(u'Необходимо указать приоритетные ДОУ или возможность зачисления в любой ДОУ')
        return super(RequestionPrefSadiksMixin, self).clean(*args, **kwargs)


class RequestionForm(RequestionPrefSadiksMixin, FormWithDocument):
    template = TemplateFormField(destination=REQUESTION_IDENTITY,
        label=u'Тип документа')
    pref_sadiks = forms.ModelMultipleChoiceField(label=u'Выберите приоритетные ДОУ',
        required=False, widget=PrefSadiksJS(),
        queryset=Sadik.objects.filter(active_registration=True),
        help_text=u'Этот список не даёт прав на внеочередное зачисление в выбранные ДОУ')

    class Meta:
        model = Requestion
        _base_fields = ['areas', 'agent_type',
                        'birth_date', 'last_name', 'first_name',
                        'patronymic', 'sex', 'template',
                        'document_number',
                        'pref_sadiks', 'location']
        if settings.DESIRED_DATE != settings.DESIRED_DATE_NO:
            _base_fields += ['admission_date',]
        if settings.DESIRED_SADIKS == settings.DESIRED_SADIKS_CHOICE:
            _base_fields = _base_fields + ['distribute_in_any_sadik',]
        fields = _base_fields

    def __init__(self, *args, **kwds):
        map_widget = admin.site._registry[Address].get_map_widget(Address._meta.get_field_by_name('coords')[0])
        self.base_fields['location'].widget = map_widget()
        self.base_fields['location'].required = True
        self.base_fields['template'].help_text = u"Документ, идентифицирующий\
            ребенка"
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


class ChangeRequestionForm(forms.ModelForm):

    class Meta:
        model = Requestion
        _base_fields = ('last_name', 'first_name',
            'patronymic', 'sex', 'location')
        if settings.DESIRED_DATE == settings.DESIRED_DATE_NO:
            fields = _base_fields
        else:
            fields = _base_fields + ('admission_date',)

    def __init__(self, *args, **kwds):
        map_widget = admin.site._registry[Address].get_map_widget(Address._meta.get_field_by_name('coords')[0])
        self.base_fields['location'].widget = map_widget()
        self.base_fields['location'].required = True
        super(ChangeRequestionForm, self).__init__(*args, **kwds)


class ProfileChangeForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ('last_name', 'first_name', 'patronymic', 'phone_number',
            'mobile_number')

    def __init__(self, *args, **kwargs):
        super(ProfileChangeForm, self).__init__(*args, **kwargs)
        self.fields['phone_number'].widget = forms.TextInput(attrs={'data-mask': '+7-999-99-99999'})
        self.fields['mobile_number'].widget = forms.TextInput(attrs={'data-mask': '+7-999-99-99999'})


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
        required=False, widget=PrefSadiksJS())

    class Meta:
        model = Requestion
        _base_fields = ('areas', 'pref_sadiks',)
        if settings.DESIRED_SADIKS == settings.DESIRED_SADIKS_CHOICE:
            _base_fields = _base_fields + ('distribute_in_any_sadik',)
        fields = _base_fields


class DocumentForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.fields['template'].queryset = EvidienceDocumentTemplate.objects.filter(
            destination=BENEFIT_DOCUMENT)