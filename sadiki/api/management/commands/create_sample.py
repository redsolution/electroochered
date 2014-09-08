# -*- coding: utf-8 -*-
import gnupg
import json

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        data = json.dumps([{
            'name': u"Вася Курочкин",
            'birth_doc_type': 1,
            'birth_doc': u"Бла-бла-бла",
            'birth_date': 1408066456,
            'registration_datetime': 1408166456,
            'sender_info': u"""
            муниципалитет: Балабашский, ответственное лицо: Вася"""
        }])
        result = encrypt_data(data)
        print result


def encrypt_data(data):
    gpg = gnupg.GPG()
    encrypted_data = gpg.encrypt(data, 'aleksey')
    return encrypted_data