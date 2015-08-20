# -*- coding: utf-8 -*-
from social_auth.backends.contrib.vkontakte import VKOAuth2Backend, VKOAuth2
from social_auth.models import UserSocialAuth


class VKontakteOAuth2BackendCustom(VKOAuth2Backend):
    pass

class VKontakteOAuth2Custom(VKOAuth2):
    AUTH_BACKEND = VKontakteOAuth2BackendCustom

# Backend definition
BACKENDS = {
    'vkontakte-oauth2': VKontakteOAuth2Custom
}
