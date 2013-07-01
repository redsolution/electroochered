#-*- coding:utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import formats, dates
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
from sadiki.core.widgets import BooleanNextYearWidget, AreaWidget
from south.modelsinspector import add_introspection_rules
from time import strptime
from widgets import JqSplitDateTimeWidget, YearChoiceDateWigdet
import datetime


class JqSplitDateTimeField(forms.MultiValueField):
    widget = JqSplitDateTimeWidget

    def __init__(self, *args, **kwargs):
        """
        Have to pass a list of field types to the constructor, else we
        won't get any data to our compress method.
        """
        all_fields = (
            forms.DateField(),
            forms.CharField(max_length=2),
            forms.CharField(max_length=2),
            )
        super(JqSplitDateTimeField, self).__init__(all_fields, *args, **kwargs)

    def compress(self, data_list):
        """
        Takes the values from the MultiWidget and passes them as a
        list to this function. This function needs to compress the
        list into a single object to save.
        """
        if data_list:
            if not (data_list[0] and data_list[1] and data_list[2]):
                raise forms.ValidationError(u"Заданы не все данные")
            try:
                input_time = datetime.time(int(data_list[1]),
                    int(data_list[2]))
            except ValueError:
                raise forms.ValidationError(u'Неверно задано время')
            return datetime.datetime.combine(data_list[0], input_time)
        return None


class YearChoiceFormField(forms.ChoiceField):
    """
    Виджет для отображения выбора года. Возвращает объект datetime с числом 1 января.
    """
    widget = YearChoiceDateWigdet

    default_error_messages = {
        'invalid': _(u'Enter a valid date.'),
    }

    def __init__(self, start_year, end_year, input_formats=None, *args, **kwargs):
        super(YearChoiceFormField, self).__init__(*args, **kwargs)
        self.choices = [('%s-01-01' % y, y) for y in range(start_year, end_year)]
        self.input_formats = input_formats

    def to_python(self, value):
        value = super(YearChoiceFormField, self).to_python(value)
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        for format in self.input_formats or formats.get_format('DATE_INPUT_FORMATS'):
            try:
                return datetime.date(*strptime(value, format)[:3])
            except ValueError:
                continue
        raise ValidationError(self.error_messages['invalid'])

    def valid_value(self, value):
        """Check to see if the provided value is a valid choice"""
        for k, v in self.choices:
            if isinstance(value, datetime.date) and value.strftime('%Y-%m-%d') == smart_unicode(k):
                return True
        return False


class YearChoiceField(models.DateField):

    def __init__(self, *args, **kwds):
        start_year = kwds.get('start_year', datetime.date(datetime.date.today().year, 1, 1))
        end_year = kwds.get('end_year', datetime.date(datetime.date.today().year + 3, 1, 1))
        self.start_year, self.end_year = start_year, end_year
        super(YearChoiceField, self).__init__(*args, **kwds)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': YearChoiceFormField,
            'start_year': self.start_year.year,
            'end_year': self.end_year.year,
        }
        defaults.update(kwargs)
        return super(YearChoiceField, self).formfield(**defaults)


class BooleanNextYearFormField(forms.BooleanField):
    widget = BooleanNextYearWidget

    def to_python(self, value):
        if value:
            return None
        else:
            return datetime.date(datetime.date.today().year, 1, 1)

    def valid_value(self, value):
        if type(value) is datetime.date and value.month == 1 and value.day == 1:
            return True
        elif value is None:
            return True
        return False

class BooleanNextYearField(models.DateField):
    u"""
    Рисует флажок. Если флажок установлен - значение None, соответссвует немедлденному зачислению.
    Если есть значение типа date, проверяется что оно равно 1 января текущего года, соответвует
    зачислению в ближайшее массовое комплектование (1 сентября).
    """

    def formfield(self, **kwargs):
        defaults = {'form_class': BooleanNextYearFormField}
        defaults.update(kwargs)
        return super(BooleanNextYearField, self).formfield(**defaults)


class TemplateFormField(forms.ModelChoiceField):

    def __init__(self, destination, queryset=None, empty_label=u"---------",
            cache_choices=False, required=True, widget=None, label=None,
            initial=None, help_text=None, to_field_name=None, *args, **kwargs):
#        нам нужен первый элемент
        initial=0
        from sadiki.core.models import EvidienceDocumentTemplate
        if not queryset:
            queryset = EvidienceDocumentTemplate.objects.filter(
                destination=destination)
        super(TemplateFormField, self).__init__(queryset, empty_label,
            cache_choices, required, widget, label, initial, help_text,
            to_field_name, *args, **kwargs)


class AreaFormField(forms.ModelChoiceField):
    widget = AreaWidget

    def __init__(self, queryset, empty_label=u"---------", cache_choices=False,
                 required=True, widget=None, label=None, initial=None,
                 *args, **kwargs):
        empty_label = u"Весь муниципалитет"
        required = False
        super(AreaFormField, self).__init__(queryset, empty_label,
            cache_choices, required, widget, label,
            initial, *args, **kwargs)

    def to_python(self, value):
        # виджет должен возвращать значение совпадающее с начальным, иначе поле будет считаться измененным
        if value:
            value = value[0]
        else:
            value = None
        value = super(AreaFormField, self).to_python(value)
        if value is None:
            return []
        else:
#        т.к. у модели поле MtM, необходимо вернуть список значений
            return [value, ]

class AreaChoiceField(models.ManyToManyField):

    def formfield(self, **kwargs):
        defaults = {'form_class': AreaFormField}
        defaults.update(kwargs)
        return super(AreaChoiceField, self).formfield(**defaults)


DAYS = [(day, "%02d" % day) for day in range(1, 31)]
MONTHS = [(month, dates.MONTHS[month]) for month in range(1, 13)]


class SplitDayMonthWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (
            forms.Select(attrs=None, choices=DAYS),
            forms.Select(attrs=None, choices=MONTHS),
        )
        super(SplitDayMonthWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            day, month = value.split(".")
            return [day, month]
        return [1, 1]


class SplitDayMonthFormField(forms.MultiValueField):

    def __init__(self, *args, **kwargs):
        kwargs['widget'] = SplitDayMonthWidget
#        убираем max_length, т.к. у нас не CharField
        kwargs.pop('max_length')
        fields = (
            forms.ChoiceField(choices=DAYS),
            forms.ChoiceField(choices=MONTHS),
        )
        super(SplitDayMonthFormField, self).__init__(fields, *args, **kwargs)

    def compress(self, value_list):
        if value_list:
            return "%s.%s" % (value_list[0], value_list[1])
        return None


class SplitDayMonthField(models.CharField):

    def formfield(self, ** kwargs):
        defaults = {'form_class': SplitDayMonthFormField, }
        defaults.update(kwargs)
        return super(SplitDayMonthField, self).formfield(**defaults)


class SadikWithAreasNameField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return u"{0} ({1})".format(smart_unicode(obj), smart_unicode(obj.area))


def validate_no_spaces(value):
    if value and u' ' in value:
        raise ValidationError(u"Поле не должно содержать пробелов.")


add_introspection_rules([], ["^sadiki\.core\.fields\.AreaChoiceField"])
add_introspection_rules([], ["^sadiki\.core\.fields\.SplitDatMonthField"])
