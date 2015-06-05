# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from sadiki.core.models import Profile, Requestion
from sadiki.logger.models import Logger
from sadiki.core.workflow import MIGRATE_USER_PERSONAL_DATA
from sadiki.core.workflow import MIGRATE_CHILD_PERSONAL_DATA
from personal_data.models import ChildPersData, UserPersData

PRINT_STEP = 100


class Command(BaseCommand):
    help_text = '''Usage: manage.py migrate_personal_data'''

    def handle(self, *args, **options):
        all_profiles = Profile.objects.select_related('userpersdata').all()
        number_of_profiles = len(all_profiles)
        prepared_profiles = 0
        print u'Обрабатываем персональные данные пользователей'
        for profile in all_profiles:
            user = profile.user
            pdata = profile.userpersdata
            new_data = {}
            # если есть персональные данные в модуле, сначала переносим их
            if pdata:
                if not user.first_name and not user.last_name:
                    user.first_name = pdata.first_name
                    user.last_name = pdata.last_name
                    new_data['first_name'] = pdata.first_name
                    new_data['last_name'] = pdata.last_name
                    profile.middle_name = pdata.second_name
                    new_data['middle_name'] = pdata.second_name
                profile.town = pdata.settlement
                new_data['town'] = pdata.settlement
                profile.street = pdata.street
                new_data['street'] = pdata.street
                profile.house = pdata.house
                new_data['house'] = pdata.house
                profile.mobile_number = pdata.phone
                new_data['phone'] = pdata.phone
            # Теперь, если в profile указано имя, но в user поля пустые,
            # переносим туда это имя. Теоретически, оно берётся из ВК,
            # поэтому имеет низший приоритет при переносе
            if (not user.first_name and not user.last_name
                                     and profile.first_name):
                user.first_name = profile.first_name
                new_data['first_name'] = profile.first_name
            profile.save()
            user.save()
            if new_data:
                Logger.objects.create_for_action(
                    MIGRATE_USER_PERSONAL_DATA,
                    context_dict={'new_data': new_data},
                    extra={'user': user},
                    reason=u'Обновление до v1.9'
                )
            prepared_profiles += 1
            if prepared_profiles % PRINT_STEP == 0:
                print u'Готово {}%'.format(
                    prepared_profiles * 100 / number_of_profiles
                )
        print u'Готово 100%\n'

        print u'Обрабатываем персональные данные детей'
        all_child_personal_data = ChildPersData.objects.all()
        number_of_child_pdata = len(all_child_personal_data)
        prepared_child_pdata = 0
        for pdata in all_child_personal_data:
            new_data = {}
            requestion = pdata.application
            requestion.child_middle_name = pdata.second_name
            new_data['child_middle_name'] = pdata.second_name
            requestion.child_last_name = pdata.last_name
            new_data['child_last_name'] = pdata.last_name
            if not requestion.name:
                requestion.name = pdata.first_name
                new_data['child_first_name'] = pdata.first_name
            requestion.save()
            Logger.objects.create_for_action(
                MIGRATE_CHILD_PERSONAL_DATA,
                context_dict={'new_data': new_data},
                extra={'user': requestion.profile.user},
                reason=u'Обновление до v1.9'
            )
            prepared_child_pdata += 1
            if prepared_child_pdata % PRINT_STEP == 0:
                print u'Готово {}%'.format(
                    prepared_child_pdata * 100 / number_of_child_pdata
                )
        print u'Готово 100%\n'
