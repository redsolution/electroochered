# -*- coding: utf-8 -*-
from social.backends.vk import VKOAuth2


class VKOAuth2Custom(VKOAuth2):
    name = 'vkontakte-oauth2'

# class VKontakteOAuth2Custom(VKOAuth2):
#     AUTH_BACKEND = VKontakteOAuth2BackendCustom

# Backend definition
BACKENDS = {
    'vkontakte-oauth2': VKOAuth2Custom
    'vk-oauth2': VKOAuth2
}
