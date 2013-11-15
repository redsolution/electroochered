# -*- coding: utf-8 -*-
from social_auth.backends.contrib.vkontakte import VKontakteOAuth2Backend, VKontakteOAuth2
from social_auth.models import UserSocialAuth


class VKontakteOAuth2BackendCustom(VKontakteOAuth2Backend):
    pass

class VKontakteOAuth2Custom(VKontakteOAuth2):
    AUTH_BACKEND = VKontakteOAuth2BackendCustom

# Backend definition
BACKENDS = {
    'vkontakte-oauth2': VKontakteOAuth2Custom
}