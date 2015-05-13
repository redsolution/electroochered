# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from sadiki.core.models import Profile, Requestion
from personal_data.models import ChildPersData, UserPersData


class Command(BaseCommand):
    help_text = '''Usage: manage.py migrate_first_name'''

    def handle(self, *args, **options):
        profiles = Profile.objects.all()
        for profile in profiles:
            if not profile.user.first_name and profile.first_name:
                profile.user.first_name = profile.first_name
                profile.user.save()
