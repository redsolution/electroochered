# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.models import Permission
from sadiki.social_auth_custom.pipeline import SingleAssociationException, AlreadyRegisteredException, NotRegisteredException
from sadiki.core.models import Profile
from sadiki.core.utils import get_unique_username
from social.apps.django_app.default.models import UserSocialAuth
from social.exceptions import AuthAlreadyAssociated


def social_user(backend, uid, user=None, *args, **kwargs):
    u"""
    В этой функции можно отследить тип операции (регистрация, логин, привязка)
    Посылаем django-сообщения в зависимости от этого типа
    social указывает на наличие соответствий "пользователь ЭО" <-> "аккаунт ВК"
    user - текущий пользователь ЭО, инициировавший процесс аутентификации
    """
    request = backend.strategy.request
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    if social:
        if user and social.user != user:
            msg = 'This {0} account is already in use.'.format(provider)
            raise AuthAlreadyAssociated(backend, msg)
        elif not user:
            user = social.user
            messages.success(request, u"Вход через ВКонтакте успешно выполнен")
    elif user:
        if user.social_auth.filter(provider=provider).exists():
            raise SingleAssociationException(
                u"Для пользователя может быть задан только "
                u"один профиль во ВКонтакте.")
        messages.success(request, u"Привязка страницы ВКонтакте к профилю "
                         u"{} успешно выполнена".format(user.username))
    else:
        messages.info(request, u"Вы успешно зарегистрировались в системе")
    return {'social': social,
            'user': user,
            'is_new': user is None,
            'new_association': False}


def create_user(backend, details, response, uid, username, user=None, *args,
                **kwargs):
    """Create user. Depends on get_username pipeline."""
    if user:
        return {'user': user}
    if not username:
        return None
    user = UserSocialAuth.create_user(username=get_unique_username(), )
    permission = Permission.objects.get(codename=u'is_requester')
    user.user_permissions.add(permission)
    profile = Profile.objects.create(user=user)
    user.set_username_by_id()
    user.save()
    return {
        'user': user,
        'is_new': True
    }


def update_user_info(backend, details, response, user=None, is_new=False,
                        *args, **kwargs):
    """Complete auth process. Return authenticated user or None."""
    profile = user.profile
    new_association = kwargs.get('new_association')
    if new_association:
        # если идет привязка к аккаунту, то получаем данные
        if backend.name == 'vkontakte-oauth2':
            profile.update_vkontakte_data(response)
    return None
