# -*- coding: utf-8 -*-
from django import template

register = template.Library()

@register.filter
def logger_messages_for_user(queue, user):
    u"""возвращает элемент с индексом index"""
    return queue.filter_for_user(user)
