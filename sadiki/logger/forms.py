# -*- coding: utf-8 -*-
from django import forms
from sadiki.core.models import AgeGroup
from sadiki.core.widgets import JqueryUIDateWidget
from sadiki.logger.models import REPORT_DECISION_CHOICES


class ReportDateForm(forms.Form):
    from_date = forms.DateField(
        label=u"Начало периода", widget=JqueryUIDateWidget)
    to_date = forms.DateField(
        label=u"Конец периода", widget=JqueryUIDateWidget)


class ReportAgeGroupForm(forms.Form):
    age_group = forms.ModelChoiceField(label=u"Возрастная группа",
        queryset=AgeGroup.objects.all())
    from_date = forms.DateField(
        label=u"Начало периода", widget=JqueryUIDateWidget)
    to_date = forms.DateField(
        label=u"Конец периода", widget=JqueryUIDateWidget)


class ReportDecisionForm(forms.Form):
    decision_type = forms.ChoiceField(choices=REPORT_DECISION_CHOICES,
        initial=0, widget=forms.RadioSelect, label=u"Тип комплектования")
    age_group = forms.ModelChoiceField(label=u"Возрастная группа",
        queryset=AgeGroup.objects.all())
    from_date = forms.DateField(
        label=u"Начало периода", widget=JqueryUIDateWidget)
    to_date = forms.DateField(
        label=u"Конец периода", widget=JqueryUIDateWidget)
