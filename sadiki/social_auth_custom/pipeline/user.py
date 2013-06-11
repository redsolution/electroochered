# -*- coding: utf-8 -*-
from django.contrib.auth.models import Permission
from sadiki.social_auth_custom.pipeline import SingleAssociationException
from sadiki.core.models import Profile
from sadiki.core.utils import get_unique_username
from social_auth.models import UserSocialAuth


def check_single_association(backend, details, response, user=None, is_new=False,
                        *args, **kwargs):
    u"""
    Проверяем нет ли у пользователя ассоциации для заданного бекэнда
    """
    social_user = kwargs.get('social_user')
    new_association = kwargs.get('new_association')
    if new_association and user.social_auth.filter(provider=backend.name).exclude(id=social_user.id).exists():
        raise SingleAssociationException(u"Для пользователя может быть задан только один профиль во ВКонтакте.")
    return None


def update_user_info(backend, details, response, user=None, is_new=False,
                        *args, **kwargs):
    """Complete auth process. Return authenticated user or None."""
    profile = user.get_profile()
    new_association = kwargs.get('new_association')
    if new_association:
        # если идет привязка к аккаунту, то получаем данные
        if backend.name == 'vkontakte-oauth2':
            profile.update_vkontakte_data(response)
            profile.save()
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