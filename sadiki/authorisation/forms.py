# -*- coding: utf-8 -*- 
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from sadiki.authorisation.models import VerificationKey
from sadiki.core.utils import get_user_by_email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label=u'Имя пользователя', max_length=75,
        widget=forms.TextInput(attrs={'placeholder': u'Введите имя пользователя, выданное при регистрации'}))

    def __init__(self, *args, **kwargs):
        self.base_fields['password'].widget = forms.PasswordInput(
            attrs={'placeholder': u'Введите пароль'})
        return super(LoginForm, self).__init__(*args, **kwargs)


class EmailResetForm(forms.Form):
    email = forms.EmailField(label=u'Адрес электронной почты')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            user = get_user_by_email(email)
            if not user:
                raise forms.ValidationError(u'''Нет пользователя с 
                    таким адресом электронной почты или адрес не подтвержден''')
            else:
                self.user_with_email = user
        return self.cleaned_data

    def save(self):
        # Отправка Email с ключом для сброса пароля
        verification_key_object = VerificationKey.objects.create_key(
            self.user_with_email)
        verification_key_object.send_reset_password()
        return self.user_with_email
