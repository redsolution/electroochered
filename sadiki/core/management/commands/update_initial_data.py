# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from sadiki.core.models import BenefitCategory
from sadiki.core.permissions import ALL_PERMISSIONS, GROUPS
from django.contrib.auth.models import Permission, User, Group
from django.contrib.contenttypes.models import ContentType
from sadiki.core.settings import WITHOUT_BENEFIT_PRIORITY


class Command(BaseCommand):
    help = "Create default permissions and groups from core/permisisons.py"

    def handle(self, *args, **options):
        #создаем необходимые роли и группы
        target_ct = ContentType.objects.get_for_model(User)
        for codename, name in ALL_PERMISSIONS:
            if not Permission.objects.filter(content_type=target_ct,
                codename=codename).exists():
                perm, created = Permission.objects.get_or_create(name=name,
                    codename=codename, content_type=target_ct)
                if created:
                    print u'Ключ доступа "%s" создан' % name
        for group_name, group_permissions in GROUPS:
            if not Group.objects.filter(name=group_name).exists():
                new_group = Group.objects.create(name=group_name)
                for codename in group_permissions:
                    perm = Permission.objects.get(codename=codename, content_type=target_ct)
                    new_group.permissions.add(perm)
                print u'Создана новая группа: %s, ключи доступа: %s' % (group_name, ', '.join(group_permissions))
        #создаем категорию Без льгот
        benefit_category, created = BenefitCategory.objects.get_or_create(priority=WITHOUT_BENEFIT_PRIORITY, defaults={'name': u"Без льгот"})
        if created:
            print u"Создана категория льгот 'Без льгот'"