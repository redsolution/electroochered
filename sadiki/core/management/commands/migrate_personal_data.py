# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from sadiki.core.models import Profile, Requestion
from personal_data.models import ChildPersData, UserPersData


class Command(BaseCommand):
    help_text = '''Usage: manage.py migrate_personal_data'''

    def handle(self, *args, **options):
        print u'Переносим Ф.И.О. заявителей'
        pdatas = UserPersData.objects.all()
        for pdata in pdatas:
            profile = pdata.profile
            user = profile.user
            if not user.first_name and pdata.first_name:
                user.first_name = pdata.first_name
                user.last_name = pdata.last_name
                user.save()
                profile.middle_name = pdata.second_name
                profile.save()
        profiles = Profile.objects.all()
        for profile in profiles:
            user = profile.user
            if not user.first_name and profile.first_name:
                user.first_name = profile.first_name
                user.save()

        print u'Переносим прочие данные заявителей'
        pdatas = UserPersData.objects.all()
        for pdata in pdatas:
            profile = pdata.profile
            profile.town = pdata.settlement
            profile.street = pdata.street
            profile.house = pdata.house
            profile.mobile_number = pdata.phone
            profile.save()

        print u'Переносим данные заявок'
        reqdatas = ChildPersData.objects.all()
        for reqdata in reqdatas:
            requestion = reqdata.application
            requestion.child_middle_name = reqdata.second_name
            requestion.child_last_name = reqdata.last_name
            if not requestion.name:
                requestion.name = reqdata.first_name
            requestion.save()
