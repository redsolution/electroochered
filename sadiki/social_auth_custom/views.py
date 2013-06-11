# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView, View
from sadiki.account.views import AccountPermissionMixin
from sadiki.core.utils import check_url
from sadiki.operator.views.base import OperatorPermissionMixin
from social_auth.backends.contrib.vkontakte import VK_DEFAULT_DATA, vkontakte_api
from social_auth.utils import setting
from social_auth.db.django_models import UserSocialAuth


class AccountSocialAuthCleanData(AccountPermissionMixin, TemplateView):
    template_name = 'social_auth/clean_data.html'

    def dispatch(self, request, *args, **kwargs):
        redirect_to = request.REQUEST.get('next', '')
        redirect_to = check_url(redirect_to, reverse('frontpage'))
        user = request.user
        return super(AccountSocialAuthCleanData, self).dispatch(
            request=request, user=user, redirect_to=redirect_to, *args, **kwargs)

    def post(self, request, user, redirect_to):
        if request.POST.get('confirmation') == 'yes':
            profile = user.profile
            profile.social_auth_clean_data()
            profile.save()
            messages.success(request, u'Данные из ВКонтакте были удалены.')
        else:
            messages.error(request, u'Данные из ВКонтакте не были удалены.')
        return HttpResponseRedirect(redirect_to)


class OperatorSocialAuthCleanData(OperatorPermissionMixin, AccountSocialAuthCleanData):

    def dispatch(self, request, user_id, *args, **kwargs):
        redirect_to = request.REQUEST.get('next', '')
        redirect_to = check_url(redirect_to, reverse('frontpage'))
        user = get_object_or_404(User, id=user_id)
        return super(AccountSocialAuthCleanData, self).dispatch(request, user=user, redirect_to=redirect_to, *args, **kwargs)


class AccountSocialAuthUpdateData(AccountPermissionMixin, TemplateView):
    template_name = 'social_auth/update_data.html'

    def get_user_social_auth(self, user):
        user_social_auth_query = user.social_auth.filter(provider='vkontakte-oauth2')
        if user_social_auth_query:
            return user_social_auth_query[0]
        else:
            return None

    def dispatch(self, request, *args, **kwargs):
        redirect_to = request.REQUEST.get('next', '')
        redirect_to = check_url(redirect_to, reverse('frontpage'))
        user = request.user
        user_social_auth = self.get_user_social_auth(user)
        if not user_social_auth:
            raise Http404
        return super(AccountSocialAuthUpdateData, self).dispatch(request, user, user_social_auth, redirect_to=redirect_to)

    def post(self, request, user, user_social_auth, redirect_to):
        if request.POST.get('confirmation') == 'yes':
            access_token = user_social_auth.tokens.get('access_token')
            uid = user_social_auth.uid
            fields = ','.join(VK_DEFAULT_DATA + setting('VK_EXTRA_DATA', []))
            params = {'access_token': access_token,
                      'fields': fields,
                      'uids': uid}

            data = vkontakte_api('users.get', params).get('response')[0]
            profile = user.profile
            profile.update_vkontakte_data(data)
            profile.save()
            messages.success(request, u'Данные из ВКонтакте были получены.')
        else:
            messages.error(request, u'Даныне из ВКонтакте не были получены.')
        return HttpResponseRedirect(redirect_to)


class OperatorSocialAuthUpdateData(OperatorPermissionMixin, AccountSocialAuthUpdateData):

    def dispatch(self, request, user_id, *args, **kwargs):
        redirect_to = request.REQUEST.get('next', '')
        redirect_to = check_url(redirect_to, reverse('frontpage'))
        user = get_object_or_404(User, id=user_id)
        user_social_auth = self.get_user_social_auth(user)
        if not user_social_auth:
            raise Http404
        return super(AccountSocialAuthUpdateData, self).dispatch(request, user, user_social_auth, redirect_to=redirect_to)


class AccountSocialAuthDisconnect(AccountPermissionMixin, TemplateView):
    template_name = 'social_auth/disconnect.html'

    def dispatch(self, request, backend, association_id):
        redirect_to = request.REQUEST.get('next', '')
        redirect_to = check_url(redirect_to, reverse('frontpage'))
        return super(AccountSocialAuthDisconnect, self).dispatch(request, backend, association_id, redirect_to=redirect_to)

    def post(self, request, backend, association_id, redirect_to):
        if request.POST.get('confirmation') == 'yes':
            association = get_object_or_404(UserSocialAuth, id=association_id, user=request.user)
            backend.disconnect(request.user, association_id)
            profile = request.user.profile
            profile.social_auth_clean_data()
            profile.save()
        return HttpResponseRedirect(redirect_to)


class OperatorSocialAuthDisconnect(OperatorPermissionMixin, AccountSocialAuthDisconnect):

    def post(self, request, backend, association_id, redirect_to):
        if request.POST.get('confirmation') == 'yes':
            association = get_object_or_404(UserSocialAuth, id=association_id)
            user = association.user
            # оператор может отвязывать профиль только для заявителей
            if user.is_requester():
                backend.disconnect(user, association_id)
                profile = user.profile
                profile.social_auth_clean_data()
                profile.save()
            else:
                raise HttpResponseForbidden(u'Вы можете работать только с заявителями')
        return HttpResponseRedirect(redirect_to)