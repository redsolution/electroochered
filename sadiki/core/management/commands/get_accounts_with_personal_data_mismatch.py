# -*- coding: utf-8 -*-
import csv
import getpass
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from sadiki.core.models import Profile, Requestion


class Command(BaseCommand):
    help_text = '''Usage: manage.py migrate_personal_data'''

    def handle(self, *args, **options):
        if 'personal_data' not in settings.INSTALLED_APPS:
            print u'Модуль персональных данных не установлен!'
            return
        from personal_data.models import ChildPersData, UserPersData
        filename = '/srv/{user}/{user}.csv'.format(user=getpass.getuser())
        f = open(filename, 'w')
        writer = csv.writer(f)
              
        # username + ссылка для оператора
        writer.writerow(['Имя пользователя', 'Ссылка на профиль для оператора'])
        link_template = 'http://{}/operator/profile/{}/'.format(
            getpass.getuser(), '{}')
        for pdata in UserPersData.objects.all():
            profile = pdata.profile
            user = profile.user
            if (profile.first_name and pdata.first_name and
                    profile.first_name != pdata.first_name):
                operator_link = link_template.format(profile.id)
                writer.writerow([user.username, operator_link])
        f.close()
