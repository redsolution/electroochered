# -*- coding: utf-8 -*-
from social_auth.exceptions import SocialAuthBaseException


class SingleAssociationException(SocialAuthBaseException):
    u"""
    Ошибка в случае, если у пользователя уже есть привязка через данный бэкенд
    """
    pass
