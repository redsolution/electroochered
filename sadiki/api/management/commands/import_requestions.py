# -*- coding: utf-8 -*-
import sys
import gnupg
import json

from django.core.management.base import BaseCommand

from sadiki.api.utils import create_requestion


class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(sys.argv) > 2:
            for f in sys.argv[2:]:
                data = open(f, 'r').read()
                decrypted_data = decrypt_data(data)
                data = json.loads(str(decrypted_data))
                for item in data:
                    req = create_requestion(item)
                    print req
        else:
            data = sys.stdin.read()
            decrypted_data = decrypt_data(data)
            data = json.loads(str(decrypted_data))
            for item in data:
                req = create_requestion(item)
                print req


def decrypt_data(data):
    gpg = gnupg.GPG()
    decrypted_data = gpg.decrypt(data)
    return decrypted_data