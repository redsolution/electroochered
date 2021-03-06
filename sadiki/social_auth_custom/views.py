# -*- coding: utf-8 -*-
import json
import urllib2

from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.generic.base import TemplateView, View
from sadiki.account.views import AccountPermissionMixin
from sadiki.core.models import Profile
from sadiki.core.utils import check_url
from sadiki.operator.views.base import OperatorPermissionMixin
from social.backends.vk import vk_api
from social.exceptions import WrongBackend
from social.apps.django_app.default.models import UserSocialAuth
from social.apps.django_app.views import auth, complete, disconnect


VK_DEFAULT_DATA = ['first_name', 'last_name', 'screen_name',
                   'nickname', 'photo']


class AccountSocialAuthDataRemove(AccountPermissionMixin, View):

    def dispatch(self, request):
        profile = request.user.profile
        return super(AccountSocialAuthDataRemove, self).dispatch(request, profile)

    def post(self, request, profile):
        if request.is_ajax():
            field = request.POST.get("field")
            if field == "skype":
                profile.skype = None
            else:
                return HttpResponse(content=json.dumps({'ok': False}),
                                    content_type='text/javascript')
            profile.save()
            return HttpResponse(content=json.dumps({'ok': True}),
                                content_type='text/javascript')
        else:
            return HttpResponseBadRequest()


class OperatorSocialAuthDataRemove(OperatorPermissionMixin, AccountSocialAuthDataRemove):

    def dispatch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        profile = user.profile
        return super(AccountSocialAuthDataRemove, self).dispatch(request, profile)


class AccountSocialAuthDataUpdate(AccountPermissionMixin, View):

    def get_user_social_auth(self, user):
        user_social_auth_query = user.social_auth.filter(provider='vkontakte-oauth2')
        if user_social_auth_query:
            return user_social_auth_query[0]
        else:
            return None

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        user_social_auth = self.get_user_social_auth(user)
        if not user_social_auth:
            raise Http404
        return super(AccountSocialAuthDataUpdate, self).dispatch(request, user, user_social_auth)

    def post(self, request, user, user_social_auth):
        if request.is_ajax():
            profile = user.profile
            access_token = user_social_auth.tokens.get('access_token')
            uid = user_social_auth.uid
            fields = ','.join(VK_DEFAULT_DATA + settings.get('VK_EXTRA_DATA', []))
            params = {'access_token': access_token,
                      'fields': fields,
                      'uids': uid}
            raw_data = vk_api('users.get', params).get('response')
            if not raw_data:
                return HttpResponse(content=json.dumps({'ok': True}),
                                    content_type='text/javascript')
            data = raw_data[0]
            field = request.POST.get("field")
            if field == "first_name":
                field_value = data.get('first_name')
                if field_value and not (profile.first_name or profile.last_name
                                        or profile.middle_name):
                    profile.first_name = field_value
            elif field == "phone_number":
                field_value = data.get('home_phone')
                if not profile.phone_number:
                    profile.phone_number = field_value
                elif not profile.mobile_number:
                    profile.mobile_number = field_value
            elif field == "skype":
                field_value = data.get('skype')
                profile.skype = field_value
            else:
                return HttpResponse(content=json.dumps({'ok': False}),
                                    content_type='text/javascript')
            profile.save()
            return HttpResponse(
                content=json.dumps({'ok': True, 'field_value': field_value}),
                content_type='text/javascript')
        else:
            return HttpResponseBadRequest()


class OperatorSocialAuthDataUpdate(OperatorPermissionMixin, AccountSocialAuthDataUpdate):

    def dispatch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user_social_auth = self.get_user_social_auth(user)
        if not user_social_auth:
            raise Http404
        return super(AccountSocialAuthDataUpdate, self).dispatch(request, user, user_social_auth)


class AccountSocialAuthDisconnect(AccountPermissionMixin, TemplateView):
    template_name = 'social_auth/disconnect.html'

    def dispatch(self, request, backend, association_id):
        redirect_to = request.GET.get('next') or request.POST.get('next', '')
        redirect_to = check_url(redirect_to, reverse('frontpage'))
        return super(AccountSocialAuthDisconnect, self).dispatch(request, backend, association_id, redirect_to=redirect_to)

    def post(self, request, backend, association_id, redirect_to):
        if request.POST.get('confirmation') == 'yes':
            association = get_object_or_404(UserSocialAuth, id=association_id, user=request.user)
            disconnect(request, backend, association_id=association_id)
            profile = request.user.profile
            profile.social_auth_clean_data()
        return HttpResponseRedirect(redirect_to)


class OperatorSocialAuthDisconnect(OperatorPermissionMixin, AccountSocialAuthDisconnect):

    def post(self, request, backend, association_id, redirect_to):
        if request.POST.get('confirmation') == 'yes':
            association = get_object_or_404(UserSocialAuth, id=association_id)
            user = association.user
            # оператор может отвязывать профиль только для заявителей
            if user.is_requester():
                disconnect(request, backend, association_id=association_id)
                profile = user.profile
                profile.social_auth_clean_data()
            else:
                return HttpResponseForbidden(u'Вы можете работать только с заявителями')
        return HttpResponseRedirect(redirect_to)
