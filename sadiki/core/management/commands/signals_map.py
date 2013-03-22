# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import csv
import re


def get_functions_names_for_signal(signal, transition):
    functions_names = []
#   проходимся по всем функциям, которые привязаны к сигналу
#   (вернее по враперам) см. listen_transitions
    for receiver in signal.receivers:
        wrapper = receiver[1]()
#       получаем переменные, которые находятся в области видимости
#       враппера
        func_cell, transitions_cell = wrapper.func_closure
        transitions = transitions_cell.cell_contents
        if transition.index in transitions:
#           при данном переходе будет вызвана функция
            func = func_cell.cell_contents
            functions_names.append(func.__name__)
    return functions_names


class Command(BaseCommand):

    def handle(self, *args, **options):
        from sadiki.core.signals import pre_status_change, post_status_change
        from sadiki.core.workflow import workflow
        available_transitions = workflow.transitions
        available_transitions = filter(
            lambda transition: transition.required_permissions,
            available_transitions)
        available_transitions = sorted(available_transitions,
            key=lambda transition: transition.index)
        f = open('signals_map.csv', 'wb')
        writer = csv.writer(f, delimiter=';',
            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for transition in available_transitions:
            pre_functions_names = get_functions_names_for_signal(
                pre_status_change, transition)
            post_functions_names = get_functions_names_for_signal(
                post_status_change, transition)
            permission_cb_name = transition.permission_cb.__name__ \
                if transition.permission_cb else u''
            writer.writerow(
                [transition.index, transition.comment.encode('utf-8'),
                    '\n'.join(pre_functions_names) or '',
                    '\n'.join(post_functions_names) or '',
                    permission_cb_name])
        f.close()
