# -*- coding: utf-8 -*-
import fileinput
import sys
import gnupg
import json

from smtplib import SMTPException
from django.template.loader import render_to_string
from django.template.context import Context
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.core.management.base import BaseCommand
from sadiki.core.models import Distribution, \
    STATUS_ON_DISTRIBUTION, Requestion, DISTRIBUTION_STATUS_END, STATUS_REQUESTER, STATUS_ON_TEMP_DISTRIBUTION, STATUS_TEMP_DISTRIBUTED, VACANCY_STATUS_DISTRIBUTED, VACANCY_STATUS_MANUALLY_CHANGED, VACANCY_STATUS_MANUALLY_DISTRIBUTING, VACANCY_STATUS_PROVIDED, Vacancies, STATUS_DECISION, DISTRIBUTION_STATUS_ENDING, SadikGroup, VACANCY_STATUS_NOT_PROVIDED
import datetime
import sadiki.core.utils
from sadiki.api.utils import create_requestion


class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(sys.argv) > 2:
            for f in sys.argv[2:]:
                print "Using file, {}".format(f)
                data = open(f, 'r').read()
                decrypted_data = decrypt_data(data)
                req = create_requestion(decrypted_data)
                print req
        else:
            print "read from stdin"
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