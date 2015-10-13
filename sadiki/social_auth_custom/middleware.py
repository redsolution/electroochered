# -*- coding: utf-8 -*-
import six

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.api import MessageFailure
from django.shortcuts import redirect
from django.utils.http import urlquote

from requests.exceptions import HTTPError
from social.exceptions import SocialAuthBaseException, AuthAlreadyAssociated
from social.utils import social_logger
from sadiki.social_auth_custom.pipeline import SingleAssociationException


class SocialAuthExceptionMiddlewareCustom(object):
    """Middleware that handles Social Auth AuthExceptions by providing the user
    with a message, logging an error, and redirecting to some next location.

    By default, the exception message itself is sent to the user and they are
    redirected to the location specified in the SOCIAL_AUTH_LOGIN_ERROR_URL
    setting.

    This middleware can be extended by overriding the get_message or
    get_redirect_uri methods, which each accept request and exception.
    """
    def process_exception(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        if strategy is None or self.raise_exception(request, exception):
            return

        if isinstance(exception, SocialAuthBaseException):
            if isinstance(exception, AuthAlreadyAssociated):
                messages.error(request, u"""Данная учетная запись ВКонтакте уже привязана к другому профилю.
                    Для завершения операции необходимо отвязать учетную запись в другом профиле.""")
                return redirect('frontpage')
            elif isinstance(exception, SingleAssociationException):
                messages.error(request, u"К одному профилю можно привязать только одну учетную запись ВКонтакте.")
                return redirect('frontpage')
            else:
                backend = getattr(request, 'backend', None)
                backend_name = getattr(backend, 'name', 'unknown-backend')

                message = self.get_message(request, exception)
                social_logger.error(message)

                url = self.get_redirect_uri(request, exception)
                try:
                    messages.error(request, message,
                                   extra_tags='social-auth ' + backend_name)
                except MessageFailure:
                    url += ('?' in url and '&' or '?') + \
                           'message={0}&backend={1}'.format(urlquote(message),
                                                            backend_name)
                return redirect(url)
        if isinstance(exception, HTTPError):
            if exception.response.status_code == 401:
                messages.error(request,
                               u"При авторизации через ВКонтакте "
                               u"произошла ошибка. Попробуйте ещё раз.")
            if request.user.is_anonymous():
                return redirect('login')
            else:
                return redirect('frontpage')

    def raise_exception(self, request, exception):
        u"""
        Обрабатываем исключения даже в режиме DEBUG
        """
        strategy = getattr(request, 'social_strategy', None)
        if strategy is not None:
            return strategy.setting('RAISE_EXCEPTIONS', False)

    def get_message(self, request, exception):
        return six.text_type(exception)

    def get_redirect_uri(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        return strategy.setting('LOGIN_ERROR_URL')
