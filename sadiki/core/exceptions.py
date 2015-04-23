# -*- coding: utf-8 -*-
class TransitionNotRegistered(Exception):
    u"""Для заявки выполнена недопустимая смена статуса"""
    pass


class TransitionNotAllowed(Exception):
    u"""Условия для успешного изменения статуса не соблюдены"""
    pass


class RequestionHidden(Exception):
    pass
