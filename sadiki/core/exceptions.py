# -*- coding: utf-8 -*-
class TransitionNotRegistered(Exception):
    u"""Для заявки выполнена недопустимая смена статуса"""
    def __init__(self, requestion=None, src=None, dst=None):
        self.requestion = requestion
        self.src_status = src
        self.dst_status = dst
        self.message = self.get_error_message()

    def get_error_message(self):
        if self.requestion:
            return u"Для заявки {} выполнена недопустимая смена статуса".format(
                self.requestion.requestion_number)
        return u"Для заявки выполнена недопустимая смена статуса"

    def __str__(self):
        return self.message


class TransitionNotAllowed(Exception):
    u"""Условия для успешного изменения статуса не соблюдены"""
    pass


class RequestionHidden(Exception):
    pass
