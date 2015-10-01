# -*- coding: utf-8 -*-
from social.apps.django_app.default.models import UserSocialAuth


class UserSocialAuthCustom(UserSocialAuth):
    class Meta:
        proxy = True
