# -*- coding: utf-8 -*- 
from django import forms
from sadiki.core.fields import JqSplitDateTimeField
from sadiki.core.models import Requestion, Sadik
from sadiki.core.widgets import JqSplitDateTimeWidget, JqueryUIDateWidget
from sadiki.operator.forms import ConfirmationForm


class RegistrationDateTimeForm(forms.ModelForm):
    registration_datetime = JqSplitDateTimeField(
        widget=JqSplitDateTimeWidget(
            attrs={'date_class': 'datepicker textInput',
                   'time_class': 'timepicker textInput'}),
        label=u'Дата подачи заявки',
        help_text=u'''
        Укажите дату когда была принята заявка от пользователя.
        Время учитывается при определении последовательности заявок в очереди.
        ''')

    class Meta:
        model = Requestion
        fields = ['registration_datetime', ]

    def __init__(self, *args, **kwargs):
        super(RegistrationDateTimeForm, self).__init__(*args, **kwargs)


class BirthDateForm(forms.ModelForm):
    birth_date = forms.DateField(
        label=u"Дата рождения", widget=JqueryUIDateWidget)

    class Meta:
        model = Requestion
        fields = ['birth_date', ]

    def __init__(self, *args, **kwargs):
        super(BirthDateForm, self).__init__(*args, **kwargs)


class DistributionByResolutionForm(ConfirmationForm):
    sadik = forms.ModelChoiceField(
        label=u"Выберите ДОУ, в который будет производиться зачисление",
        queryset=Sadik.objects.all())
    resolutioner_post = forms.CharField(
        label=u"Должность резолюционера", max_length=255)
    resolutioner_fio = forms.CharField(
        label=u"ФИО резолюционера", max_length=255)
    resolution_number = forms.CharField(
        label=u"Номер документа", max_length=255)

    def __init__(self, requestion, *args, **kwargs):
        age_groups = requestion.age_groups()
        age_groups_ids = [age_group.id for age_group in age_groups]
        self.base_fields['sadik'].queryset = Sadik.objects.filter(
            age_groups__id__in=age_groups_ids)
        super(DistributionByResolutionForm, self).__init__(
            requestion, *args, **kwargs)