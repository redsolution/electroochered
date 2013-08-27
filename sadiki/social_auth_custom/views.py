# -*- coding: utf-8 -*-
import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView, View
from sadiki.account.views import AccountPermissionMixin
from sadiki.core.models import Profile
from sadiki.core.utils import check_url
from sadiki.operator.views.base import OperatorPermissionMixin
from social_auth.backends import get_backend
from social_auth.backends.contrib.vkontakte import VK_DEFAULT_DATA, vkontakte_api
from social_auth.decorators import dsa_view
from social_auth.exceptions import WrongBackend
from social_auth.utils import setting
from social_auth.db.django_models import UserSocialAuth
from social_auth.views import associate_complete, complete_process, auth_process


class AccountSocialAuthDataRemove(AccountPermissionMixin, View):

    def dispatch(self, request):
        profile = request.user.get_profile()
        return super(AccountSocialAuthDataRemove, self).dispatch(request, profile)

    def post(self, request, profile):
        if request.is_ajax():
            field = request.POST.get("field")
            if field == "first_name":
                profile.first_name = None
            elif field == "phone_number":
                profile.phone_number = None
            elif field == "skype":
                profile.skype = None
            else:
                return HttpResponse(content=json.dumps({'ok': False}),
                        mimetype='text/javascript')
            profile.save()
            return HttpResponse(content=json.dumps({'ok': True}),
                    mimetype='text/javascript')
        else:
            return HttpResponseBadRequest()


class OperatorSocialAuthDataRemove(OperatorPermissionMixin, AccountSocialAuthDataRemove):

    def dispatch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        profile = user.get_profile()
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
            profile = user.get_profile()
            access_token = user_social_auth.tokens.get('access_token')
            uid = user_social_auth.uid
            fields = ','.join(VK_DEFAULT_DATA + setting('VK_EXTRA_DATA', []))
            params = {'access_token': access_token,
                      'fields': fields,
                      'uids': uid}
            data = vkontakte_api('users.get', params).get('response')[0]
            field = request.POST.get("field")
            if field == "first_name":
                field_value = data.get('first_name')
                profile.first_name = field_value
            elif field == "phone_number":
                field_value = data.get('home_phone')
                profile.phone_number = field_value
            elif field == "skype":
                field_value = data.get('skype')
                profile.skype = field_value
            else:
                return HttpResponse(content=json.dumps({'ok': False}),
                        mimetype='text/javascript')
            profile.save()
            return HttpResponse(content=json.dumps({'ok': True, 'field_value': field_value}),
                    mimetype='text/javascript')
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
        redirect_to = request.REQUEST.get('next', '')
        redirect_to = check_url(redirect_to, reverse('frontpage'))
        return super(AccountSocialAuthDisconnect, self).dispatch(request, backend, association_id, redirect_to=redirect_to)

    def post(self, request, backend, association_id, redirect_to):
        if request.POST.get('confirmation') == 'yes':
            association = get_object_or_404(UserSocialAuth, id=association_id, user=request.user)
            backend.disconnect(request.user, association.id)
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


class CustomAuth(View):
    def get_redirect(self, backend):
        raise NotImplementedError

    def get(self, request, backend):
        request.social_auth_backend = get_backend(backend, request, self.get_redirect(backend))
        if request.social_auth_backend is None:
            raise WrongBackend(backend)
        return auth_process(request, request.social_auth_backend)


class LoginAuth(CustomAuth):
    def get_redirect(self, backend):
        return reverse('socialauth_complete', kwargs={"backend": backend, "type": "login"})


class RegistrationAuth(CustomAuth):
    def get_redirect(self, backend):
        return reverse('socialauth_complete', kwargs={"backend": backend, "type": "registration"})


@csrf_exempt
@dsa_view()
def custom_complete(request, backend, type):
    if request.user.is_authenticated():
        return associate_complete(request, backend, type=type)
    else:
        return complete_process(request, backend, type=type)
