# -*- coding: utf-8 -*- 
from django import forms
from sadiki.core.fields import JqSplitDateTimeField
from sadiki.core.models import Requestion
from sadiki.core.widgets import JqSplitDateTimeWidget, JqueryUIDateWidget

class RegistrationDateTimeForm(forms.ModelForm):
    registration_datetime = JqSplitDateTimeField(
        widget=JqSplitDateTimeWidget(attrs={'date_class':'datepicker textInput', 'time_class':'timepicker textInput'}),
        label=u'Дата подачи заявки',
            help_text=u'''Укажите дату когда была принята заявка от пользователя.
                Время учитывается при определении последовательности заявок в очереди.''')

    class Meta:
        model = Requestion
        fields = ['registration_datetime', ]

    def __init__(self, *args, **kwargs):
        super(RegistrationDateTimeForm, self).__init__(*args, **kwargs)

class BirthDateForm(forms.ModelForm):
    birth_date = forms.DateField(label=u"Дата рождения",
        widget=JqueryUIDateWidget)

    class Meta:
        model = Requestion
        fields = ['birth_date', ]

    def __init__(self, *args, **kwargs):
        super(BirthDateForm, self).__init__(*args, **kwargs)
