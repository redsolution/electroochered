# -*- coding: utf-8 -*-
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.template import loader
from django.template.context import RequestContext
from sadiki.core.models import Requestion
from sadiki.core.templatetags.sadiki_core_tags import FakeWSGIRequest

ADMINISTRATOR_PERMISSION = ('is_administrator', u'Администратор системы')
OPERATOR_PERMISSION = ('is_operator', u'Оператор территориальной области')
REQUESTER_PERMISSION = ('is_requester', u'Представитель ребенка')
DISTRIBUTOR_PERMISSION = ('is_distributor', u'Ответственный за распределение')
SUPERVISOR_PERMISSION = ('is_supervisor', u'Ответственный за внештатные ситуации')
SADIK_OPERATOR_PERMISSION = ('is_sadik_operator', u'Ответственный за внештатные ситуации')

OPERATOR_GROUP_NAME = u'Реестр операторов'
ADMINISTRATOR_GROUP_NAME = u'Реестр администраторов'
DISTRIBUTOR_GROUP_NAME = u"Реестр ответственных за распределение"
SUPERVISOR_GROUP_NAME = u'Реестр ответственных за внештатные ситуации'
SADIK_OPERATOR_GROUP_NAME = u'Реестр операторов ДОУ'

# Для использования в команде updatepermissions
ALL_PERMISSIONS = [OPERATOR_PERMISSION, REQUESTER_PERMISSION,
    ADMINISTRATOR_PERMISSION, DISTRIBUTOR_PERMISSION, SUPERVISOR_PERMISSION,
    SADIK_OPERATOR_PERMISSION]
GROUPS = (
    (OPERATOR_GROUP_NAME, (OPERATOR_PERMISSION[0],)),
    (DISTRIBUTOR_GROUP_NAME, (DISTRIBUTOR_PERMISSION[0],)),
    (ADMINISTRATOR_GROUP_NAME, (ADMINISTRATOR_PERMISSION[0],)),
    (SUPERVISOR_GROUP_NAME, (SUPERVISOR_PERMISSION[0],)),
    (SADIK_OPERATOR_GROUP_NAME, (SADIK_OPERATOR_PERMISSION[0],)),
)


class RequirePermissionsMixin(object):
    u"""
    прозводит проверку наличия прав у пользователя
    у пользователя должно оказаться хотя бы одно разрешение
    """
    required_permissions = []

    def check_permissions(self, request, *args, **kwargs):
        """
        Return True if all requirements satisfied
        """
#        пройдемся по всем элементам
        return any([request.user.has_perm("auth.%s" % req) for req in self.required_permissions])

    def dispatch(self, request, *args, **kwargs):
#        если метод CHECK, то необходимо осуществить только проверку возможности выполнения
        if isinstance(request, FakeWSGIRequest):
            if self.check_permissions(request, *args, **kwargs):
                return True
            else:
                return False
        if self.check_permissions(request, *args, **kwargs):
            return super(RequirePermissionsMixin, self
                ).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden(loader.render_to_string('403.html',
                context_instance=RequestContext(request)))

class RequestionMixin(RequirePermissionsMixin):

    def dispatch(self, request, requestion_id):
        requestion = get_object_or_404(Requestion, id=requestion_id)
        return RequirePermissionsMixin.dispatch(self, request,
            current_requestion=requestion)

class RequestionTransferMixin(RequestionMixin):
    def check_permissions(self, request, current_requestion, *args, **kwags):
        from sadiki.core.workflow import workflow
        transitions_available = set(self.transitions) & set(workflow.available_transitions(
                current_requestion.status))
        return RequestionMixin.check_permissions(
            self, request, current_requestion) and transitions_available
