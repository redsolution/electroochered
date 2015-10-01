# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from social.apps.django_app.default.models import UserSocialAuth


def get_user_for_disconnect(strategy, user, name, user_storage,
                            association_id=None, *args, **kwargs):
    u"""
    Если отвязывание аккаунта проводит оператор, то нужно найти требуемого
    пользователя, поскольку user в данном случае - сам оператор
    """
    if association_id:
        association = get_object_or_404(UserSocialAuth, id=association_id)
        return {'user': association.user}
    return None

