# -*- coding: utf-8 -*-
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from sadiki.core.models import Sadik, Requestion, BenefitCategory
from sadiki.core.permissions import ALL_PERMISSIONS
from sadiki.core.settings import WITHOUT_BENEFIT_PRIORITY


class Command(BaseCommand):
    help = "Validate DB"

    def handle(self, *args, **options):
        requestions_not_exists = not Requestion.objects.exists()
        sadiks_not_exists = not Sadik.objects.exists()
        #validate permissions
        target_ct = ContentType.objects.get_for_model(User)
        permissions_created = all(
            [Permission.objects.filter(content_type=target_ct,
                codename=codename).exists() for codename, name in ALL_PERMISSIONS])
        benefits_created = BenefitCategory.objects.filter(priority=WITHOUT_BENEFIT_PRIORITY).exists()
        if all((requestions_not_exists, sadiks_not_exists, permissions_created,
                benefits_created)):
            print u"Ошибок не обнаружено"
        else:
            if not requestions_not_exists:
                print u"Ошибка: В БД есть заявки."
            if not sadiks_not_exists:
                print u"Ошибка: В БД есть детские сады."
            if not permissions_created:
                print u"Ошибка: В БД отсутствуют необходимые права."
            if not benefits_created:
                print u"Ошибка: В БД отсутствуют системные льготы."