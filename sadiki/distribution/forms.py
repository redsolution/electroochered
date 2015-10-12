# -*- coding: utf-8 -*-
from django import forms
from sadiki.core.models import REQUESTION_TYPE_IMPORTED
from sadiki.core.utils import reorder_fields


class SelectSadikForm(forms.Form):
    sadik = forms.ChoiceField(label=u'Выбрать МДОУ:', choices=(), widget=forms.Select())
    requestion_id = forms.IntegerField(label=u'ID заявки', widget=forms.HiddenInput())

    def __init__(self, requestion, *args, **kwargs):
        # сделать optgroups
        is_preferred_sadiks = kwargs.pop('is_preferred_sadiks', [])
        sadiks_query = kwargs.pop('sadiks_query', [])
        self.requestion = requestion

        def select_list_from_qs(queryset, requestion):
            '''Делает из queryset список для параметра choices'''
            select_list = []
            for obj in queryset:
                select_list.append((obj.id, unicode(obj)))
            return select_list

        choices = []
        if is_preferred_sadiks:
            choices.append((u'Предпочитаемые МДОУ', select_list_from_qs(sadiks_query, requestion)))
        else:
            choices.append((u'МДОУ этого района', select_list_from_qs(sadiks_query, requestion)))

        super(SelectSadikForm, self).__init__(*args, **kwargs)
        self.fields['sadik'].choices = choices
        self.fields['requestion_id'].initial = self.requestion.id
        # изменяем порядок полей
        if requestion.needs_location_confirmation:
            self.fields['accept_location'] = forms.BooleanField(label=u'Координаты на карте совпадают с адресом',)
            self.fields['accept_location'].error_messages['required'] = u'Подтвердите местоположение заявки'
            if not requestion.location:
                self.fields['accept_location'].widget.attrs['disabled'] = 'disabled'
                self.fields['accept_location'].error_messages['required'] = u'Необходимо указать местоположение заявки'
            fields_order = self.fields.keys()
            fields_order.remove('accept_location')
            fields_order.insert(0, 'accept_location')
            self.fields = reorder_fields(self.fields, fields_order)

    def clean_requestion_id(self):
        requestion_id = self.cleaned_data.get('requestion_id')
        if requestion_id == self.requestion.id:
            return requestion_id
        else:
            raise forms.ValidationError(u'Вы работаете не с последней заявкой')

    def clean(self):
        cleaned_data = self.cleaned_data
        if cleaned_data.get('accept_location') and not self.requestion.location:
            raise forms.ValidationError(u"Необходимо указать местоположение заявки")
        return cleaned_data
