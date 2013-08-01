# -*- coding: utf-8 -*-
import cPickle
from django.contrib.auth.models import User, Permission
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from sadiki.core.models import Requestion, Profile, Address, REQUESTION_TYPE_IMPORTED, Area, Sadik, Benefit, STATUS_REQUESTER, EvidienceDocumentTemplate, EvidienceDocument, AgeGroup, Preference, PREFERENCE_IMPORT_FINISHED
from sadiki.core.utils import get_unique_username


class Command(BaseCommand):
    help = "Сохранение данных для импорта из подготовленного файла"
    args = ['filename', ]

    def handle(self, *args, **options):
        if Preference.objects.filter(key=PREFERENCE_IMPORT_FINISHED).exists():
            print u"Импорт заявок уже был произведен, дальнейший импорт данных невозможен."
            return
        with transaction.commit_on_success():
            if args:
                filename = args[0]
                f = open(filename, 'r')
                p = cPickle.Unpickler(f)
                import_type = p.load()
                try:
                    while True:
                        instance_data = p.load()
                        if import_type == "requestion_import":
                            self.save_requestion(instance_data)
                        elif import_type == "sadik_import":
                            self.save_sadik(instance_data)
                        else:
                            raise CommandError(u"Неверный формат файла")
                except EOFError:
                    if import_type == "requestion_import":
                        Preference.objects.create(key=PREFERENCE_IMPORT_FINISHED)
                    f.close()
            else:
                raise CommandError(u'Необходимо ввести имя файла')

    def save_requestion(self, requestion_data):
        from sadiki.core.workflow import IMPORT_PROFILE, REQUESTION_IMPORT
        coords = requestion_data["requestion_data"].pop("coords")
        requestion = Requestion(**requestion_data['requestion_data'])
        requestion.set_location(coords)
        requestion.status = STATUS_REQUESTER
        profile = Profile()
        user = User.objects.create_user(get_unique_username(), '')
        user.set_username_by_id()
        user.save()
        permission = Permission.objects.get(codename=u'is_requester')
        user.user_permissions.add(permission)
        profile.user = user
        profile.save()
        requestion.profile = profile
        requestion.cast = REQUESTION_TYPE_IMPORTED
        requestion.save()
        document = requestion_data['document']
        if document:
            if not document['fake']:
                document_template = EvidienceDocumentTemplate.objects.get(name=document['template_name'])
            else:
                document_template = EvidienceDocumentTemplate.objects.all()[0]
            document = EvidienceDocument(
                template=document_template,
                document_number=document['document_number'], confirmed=True,
                fake=document['fake'])
        document.content_object = requestion
        document.save()
        areas_names = requestion_data['areas']
        areas = []
        for area_name in areas_names:
            area = Area.objects.get(name=area_name)
            areas.append(area)
        if areas:
            requestion.areas.add(*areas)
        preferred_sadiks = []
        for sadik_identifier in requestion_data['sadiks_identifiers_list']:
            sadik = Sadik.objects.get(identifier=sadik_identifier)
            preferred_sadiks.append(sadik)
        for sadik in preferred_sadiks:
            requestion.pref_sadiks.add(sadik)
#                добавляем льготы
        benefits = []
        for benefit_name in requestion_data['benefits_names']:
            benefit = Benefit.objects.get(name=benefit_name)
            benefits.append(benefit)
        if benefits:
            for benefit in benefits:
                requestion.benefits.add(benefit)
                requestion.save()
        context_dict = {'user': user, 'profile': profile,
                        'requestion': requestion,
                        'pref_sadiks': preferred_sadiks,
                        'areas': areas, 'benefits': benefits}
        from sadiki.logger.models import Logger
        Logger.objects.create_for_action(IMPORT_PROFILE,
            context_dict={'user': user, 'profile': profile},
            extra={'obj': profile})
        Logger.objects.create_for_action(REQUESTION_IMPORT,
            context_dict=context_dict,
            extra={'obj': requestion,
                'added_pref_sadiks': preferred_sadiks})

    def save_sadik(self, instance_data):
        sadik_data = instance_data["sadik_data"]
        sadik_data["area"] = Area.objects.get(name=sadik_data["area"])
        sadik = Sadik(**sadik_data)
        address_data = instance_data["address_data"]
        coords = instance_data["coords"]
        latitude = coords["latitude"]
        longtitude = coords["longtitude"]
        address_data.update({'coords': Point(longtitude, latitude)})
        address = Address.objects.get_or_create(**address_data)[0]
        sadik.address = address
        age_groups_names = instance_data["age_groups"]
        if age_groups_names:
            age_groups = [AgeGroup.objects.get(name=age_group_name) for age_group_name in age_groups_names]
        else:
            age_groups = AgeGroup.objects.all()
        sadik.save()
        sadik.age_groups = age_groups

