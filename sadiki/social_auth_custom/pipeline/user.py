# -*- coding: utf-8 -*-
from django.contrib.auth.models import Permission
from sadiki.social_auth_custom.pipeline import SingleAssociationException, AlreadyRegisteredException, NotRegisteredException
from sadiki.core.models import Profile
from sadiki.core.utils import get_unique_username
from social.apps.django_app.default.models import UserSocialAuth


def social_user(backend, uid, user=None, *args, **kwargs):
    u"""
    Определяем тип операции (регистрация, логин, привязка)
    """
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    if social:
        if user and social.user != user:
            msg = 'This {0} account is already in use.'.format(provider)
            raise AuthAlreadyAssociated(backend, msg)
        elif not user:
            user = social.user
            action = 'login'
        else:
            action = None   # когда пытаемся повторно привязать тот же аккаунт
    elif user:
        action = 'binding'
    else:
        action = 'registration'
    return {'social': social,
            'user': user,
            'is_new': user is None,
            'new_association': False,
            'action': action}


def check_single_association(backend, details, response, user=None,
                             is_new=False, *args, **kwargs):
    u"""
    Проверяем нет ли у пользователя ассоциации для заданного бекэнда
    """
    social = kwargs.get('social')
    new_association = kwargs.get('new_association')
    if user and not social and user.social_auth.filter(provider=backend.name).exists():
        raise SingleAssociationException(u"Для пользователя может быть задан только один профиль во ВКонтакте.")
    return None


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
