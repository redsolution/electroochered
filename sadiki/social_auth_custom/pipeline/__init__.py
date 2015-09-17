# -*- coding: utf-8 -*-
from social.exceptions import SocialAuthBaseException


class SingleAssociationException(SocialAuthBaseException):
    u"""
    Ошибка в случае, если у пользователя уже есть привязка через данный бэкенд
    """
    pass


class AlreadyRegisteredException(SocialAuthBaseException):
    u"""
    Ошибка если данный аккаунт социальной авторизвации уже привязан к профилю
    """
    pass


class NotRegisteredException(SocialAuthBaseException):
    u"""
    Ошибка если данный аккаунт социальной авторизвации не привязан к профилю
    """
    pass
