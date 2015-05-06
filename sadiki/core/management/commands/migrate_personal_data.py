# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from sadiki.core.models import Profile, Requestion
from personal_data.models import ChildPersData, UserPersData


class Command(BaseCommand):
    help_text = '''Usage: manage.py migrate_personal_data'''

    def handle(self, *args, **options):
        # переносим данные заявителей
        users_data = UserPersData.objects.all()
        for user_data in users_data:
            profile = user_data.profile
            profile.town = user_data.settlement
            profile.street = user_data.street
            profile.house = user_data.house
            profile.middle_name = user_data.second_name
            profile.last_name = user_data.last_name
            profile.mobile_number = user_data.phone
            profile.first_name = user_data.first_name
            profile.save()
        
        # переносим данные заявки
        reqs_data = ChildPersData.objects.all()
        for req_data in reqs_data:
            requestion = req_data.application
            requestion.child_middle_name = req_data.second_name
            requestion.child_last_name = req_data.last_name
            requestion.name = req_data.first_name
            requestion.save()
