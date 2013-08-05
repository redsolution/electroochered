# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.http import urlquote
from sadiki.core.models import Requestion, REQUESTION_IDENTITY
from sadiki.core.permissions import RequirePermissionsMixin
from sadiki.core.templatetags.sadiki_core_tags import FakeWSGIRequest

class OperatorPermissionMixin(RequirePermissionsMixin):
    u"""
    проверка является ли пользователь оператором
    """
    required_permissions = ['is_operator']


class OperatorRequestionMixin(OperatorPermissionMixin):

    def check_permissions(self, request, requestion, *args, **kwargs):
        if OperatorPermissionMixin.check_permissions(self, request) and request.user.perms_for_area(requestion.areas.all()):
            return True
        return False

    def dispatch(self, request, requestion_id, *args, **kwargs):
        requestion = get_object_or_404(Requestion, id=requestion_id)
        return RequirePermissionsMixin.dispatch(self, request, *args,
            requestion=requestion, **kwargs)


class OperatorRequestionCheckIdentityMixin(object):
    u"""проверяем, что у заявки указан идентифицирующий документ,
    если нет, то редирект на страницу с возможностью указать"""

    def dispatch(self, request, requestion_id, *args, **kwargs):
        requestion = get_object_or_404(Requestion, id=requestion_id)
        if not isinstance(request, FakeWSGIRequest):
            if requestion.is_fake_identity_documents():
                return HttpResponseRedirect(
                    u'%s?next=%s' %
                    (reverse('operator_requestion_set_identity_document',
                        kwargs={'requestion_id': requestion_id}),
                        urlquote(request.get_full_path()))
                    )
        return RequirePermissionsMixin.dispatch(self, request, *args,
            requestion=requestion, **kwargs)


class OperatorRequestionEditMixin(OperatorRequestionMixin):
    def check_permissions(self, request, requestion, *args, **kwargs):
        return super(OperatorRequestionEditMixin, self).check_permissions(
            request, requestion, *args, **kwargs) and requestion.editable
