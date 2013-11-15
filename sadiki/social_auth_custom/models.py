# -*- coding: utf-8 -*-
from social_auth.db.django_models import UserSocialAuth


class UserSocialAuthCustom(UserSocialAuth):
    class Meta:
        proxy = True