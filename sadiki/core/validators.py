# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
import datetime


def birth_date_validator(value):
    current_date = datetime.date.today()
    # Обрабатываем високосные года
    try:
        end_date = current_date.replace(
                year=current_date.year - settings.MAX_CHILD_AGE)
    except ValueError:
        end_date = current_date.replace(
            year=current_date.year - settings.MAX_CHILD_AGE,
            day=current_date.day - 1
        )

    if value < end_date:
        raise ValidationError(u"Возраст ребёнка превышает максимальный")
    elif value > current_date:
        raise ValidationError(u"Дата рождения не может превышать текущую дату")


def registration_date_validator(value):
    current_date = datetime.date.today()
    if value.date() > current_date:
        raise ValidationError(u"Дата регистрации не может превышать текущую дату")


snils_validator = RegexValidator(
    '^[0-9]{3}-[0-9]{3}-[0-9]{3} [0-9]{2}$',
    message=u'неверный формат'
)

passport_series_validator = RegexValidator(
    '^[0-9]{4}$',
    message=u'неверный формат',
)

passport_number_validator = RegexValidator(
    '^[0-9]{6}$',
    message=u'неверный формат',
)

phone_validator = RegexValidator(
    r'^[\d\-()+ ]*$',
    message=u'может содержать только цифры, +, -, скобки и пробелы',
)
